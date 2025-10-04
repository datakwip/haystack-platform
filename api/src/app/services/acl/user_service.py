from sqlalchemy.orm import Session, aliased
from app.services import exception_service
from sqlalchemy import or_
from app.model.sqlalchemy import source_object_model, acl_org_model, acl_user_model
from app.model.pydantic.acl.user import user_schema
from datetime import datetime
from app.services import tag_meta_service, request_service, config_service
import jwt
import requests
from fastapi import Request, HTTPException, Depends
import logging
import json

logger = logging.getLogger(__name__)

def verify_cognito_jwt(token: str):
    """
    Verify AWS Cognito JWT token by downloading and using the public keys
    """
    try:
        # Get the JWT header to find the key ID
        headers = jwt.get_unverified_header(token)
        kid = headers.get('kid')
        
        if not kid:
            raise HTTPException(status_code=403, detail="Invalid token: missing key ID")
        
        # Construct the JWKS URL for the Cognito User Pool
        region = "us-east-1"  # Should match the region in auth_service.py
        user_pool_id = config_service.user_pool_id
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        
        # Download the JWKS
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()
        
        # Find the matching key
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            raise HTTPException(status_code=403, detail="Invalid token: key not found")
        
        # First decode without verification to check if audience claim exists
        unverified_payload = jwt.decode(token, options={"verify_signature": False})

        # Verify and decode the token
        decode_options = {
            'algorithms': ['RS256'],
            'issuer': f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        }

        # Only validate audience if the token contains an 'aud' claim
        if 'aud' in unverified_payload:
            decode_options['audience'] = config_service.app_client_id

        decoded = jwt.decode(token, public_key, **decode_options)
        
        return decoded
        
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(status_code=403, detail="Invalid token")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch JWKS: {str(e)}")
        raise HTTPException(status_code=500, detail="Token validation service unavailable")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=403, detail="Token verification failed")

def get_current_user(request : Request, session, default_user_email : str = None):
    try:
        db = session
        user_id = None
        user_email = default_user_email
        if user_email is None:
            auth_token = request_service.get_auth_token(request)
            decoded = verify_cognito_jwt(auth_token)
            user_email = decoded.get("email")

            if not user_email:
                user_email = decoded.get("username")
                if not user_email:
                    logger.error({"request_id": request.state.request_id, "detail": "email and username not found in token"})
                    raise HTTPException(status_code=403, detail="Invalid token: missing email and username")
        if user_email is not None:
            user = get_user_by_email(db, user_email)
            if user is not None:
                user_id = user.id
        if user_id is None:
            logger.error({"request_id": request.state.request_id, "detail": "current user not found"})
            raise HTTPException(status_code=403, detail="not authorized")
        return user_id
    except HTTPException:
        # Re-raise HTTP exceptions as they already have proper error details
        raise
    except Exception as e:
        logger.error({"request_id": getattr(request.state, 'request_id', 'unknown'), "detail": f"Unexpected error in get_current_user: {str(e)}"})
        raise HTTPException(status_code=403, detail="not authorized")

def get_user_by_email(db : Session, user_email : str) -> acl_user_model.User:
    result = db.query(acl_user_model.User).filter(acl_user_model.User.email == user_email).first()
    if result is not None:
        return result
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def get_user_by_id(db : Session, user_id : int) -> acl_user_model.User:
    result = db.query(acl_user_model.User)\
        .filter(acl_user_model.User.id == user_id)\
        .filter(acl_user_model.User.disabled_ts == None) \
        .first()
    if result is not None:
        return result
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )


def is_user_org_admin(org_id : int, user_id: id, db: Session):
    result = db.query(acl_org_model.OrgAdmin)\
        .filter(acl_org_model.OrgAdmin.org_id == org_id)\
        .filter(acl_org_model.OrgAdmin.user_id == user_id)
    for res in result:
        return True
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied", loc=[])],
            exception_service.Ctx("")
        )
    )

def is_meta_visible_for_user(db : Session, org_id : int, user_id : int, meta_id : int):
    db_meta = tag_meta_service.get_meta_by_id(db, meta_id, org_id)

    tag_def1 = aliased(source_object_model.TagDef)
    tag_def2 = aliased(source_object_model.TagDef)

    org_tag_permission_subquery = db.query(acl_org_model.OrgTagPermission) \
        .filter(acl_org_model.OrgTagPermission.org_id == org_id) \
        .filter(acl_org_model.OrgTagPermission.tag_id == source_object_model.TagMeta.value) \
        .exists()

    user_tag_add_permission_subquery = db.query(acl_user_model.UserTagAddPermission) \
        .filter(acl_user_model.UserTagAddPermission.user_id == user_id) \
        .filter(acl_user_model.UserTagAddPermission.tag_id == source_object_model.TagMeta.value) \
        .exists()

    user_tag_rev_permission_subquery = ~db.query(acl_user_model.UserTagRevPermission) \
        .filter(acl_user_model.UserTagRevPermission.user_id == user_id) \
        .filter(acl_user_model.UserTagRevPermission.tag_id == source_object_model.TagMeta.value) \
        .exists()

    result = db.query(source_object_model.TagMeta, acl_org_model.Org, acl_user_model.User) \
        .join(tag_def1, source_object_model.TagMeta.tag_id == tag_def1.id) \
        .join(tag_def2, source_object_model.TagMeta.attribute == tag_def2.id) \
        .filter(tag_def1.disabled_ts == None) \
        .filter(tag_def2.name == "lib") \
        .filter(acl_org_model.Org.id == org_id) \
        .filter(acl_user_model.User.id == user_id) \
        .filter(source_object_model.TagMeta.tag_id == db_meta.tag_id) \
        .filter(or_((org_tag_permission_subquery), (user_tag_add_permission_subquery))) \
        .filter(user_tag_rev_permission_subquery)
    for res in result:
        return True

#    result = db.execute(
#        """select * from core_dev.tag_meta tm , core_dev.tag_def td, core_dev.org o, core_dev."user" u, core_dev.tag_def td2
#where   td.disabled_ts is null and tm.id = {} and o.id  = {} and u.id  = {} and  tm.tag_id  = td.id and td2.id = tm."attribute"  and td2.name = 'lib' and (exists (select 1 from core_dev.org_tag_permission otp where otp.tag_id = tm.value and otp.org_id  = o.id) or exists(select 1 from  core_dev.user_tag_add_permission utap where utap.user_id = u.id and utap.tag_id = tm.value))
#and not exists (select 1 from core_dev.user_tag_rev_permission utrp  where utrp.user_id = u.id and utrp.tag_id = tm.value)""".format(meta_id, org_id, user_id)
#    )
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def is_tag_visible_for_user(db : Session, org_id : int, user_id : int, tag_id : int):
    result = db.query(acl_org_model.OrgUser) \
        .filter(acl_org_model.OrgUser.user_id == user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
        .first()
    if result is not None:
        tag_def1 = aliased(source_object_model.TagDef)
        tag_def2 = aliased(source_object_model.TagDef)

        org_tag_permission_subquery = db.query(acl_org_model.OrgTagPermission)\
            .filter(acl_org_model.OrgTagPermission.org_id == org_id) \
            .filter(acl_org_model.OrgTagPermission.tag_id == source_object_model.TagMeta.value) \
            .exists()

        user_tag_add_permission_subquery = db.query(acl_user_model.UserTagAddPermission)\
            .filter(acl_user_model.UserTagAddPermission.user_id == user_id) \
            .filter(acl_user_model.UserTagAddPermission.tag_id == source_object_model.TagMeta.value) \
            .exists()

        user_tag_rev_permission_subquery = ~db.query(acl_user_model.UserTagRevPermission)\
            .filter(acl_user_model.UserTagRevPermission.user_id == user_id) \
            .filter(acl_user_model.UserTagRevPermission.tag_id == source_object_model.TagMeta.value) \
            .exists()

        result = db.query(source_object_model.TagMeta, acl_org_model.Org, acl_user_model.User)\
            .join(tag_def1, source_object_model.TagMeta.tag_id == tag_def1.id)\
            .join(tag_def2, source_object_model.TagMeta.attribute == tag_def2.id)\
            .filter( source_object_model.TagMeta.disabled_ts == None) \
            .filter(tag_def1.disabled_ts == None)\
            .filter(tag_def2.name == "lib")\
            .filter(acl_org_model.Org.id == org_id)\
            .filter(acl_user_model.User.id == user_id)\
            .filter(tag_def1.id == tag_id)\
            .filter(or_((org_tag_permission_subquery),(user_tag_add_permission_subquery)))\
            .filter(user_tag_rev_permission_subquery )
        if result is not None:
            return True

#    result = db.execute(
#        """select * from core_dev.tag_meta tm , core_dev.tag_def td, core_dev.org o, core_dev."user" u, core_dev.tag_def td2
#where   td.disabled_ts is null and td.id = {} and o.id  = {} and u.id  = {} and  tm.tag_id  = td.id and td2.id = tm."attribute"  and td2.name = 'lib' and (exists (select 1 from core_dev.org_tag_permission otp where otp.tag_id = tm.value and otp.org_id  = o.id) or exists(select 1 from  core_dev.user_tag_add_permission utap where utap.user_id = u.id and utap.tag_id = tm.value))
#and not exists (select 1 from core_dev.user_tag_rev_permission utrp  where utrp.user_id = u.id and utrp.tag_id = tm.value)""".format(tag_id, org_id, user_id)
#    )
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def is_entity_visible_for_user(db : Session, org_id : int, user_id : int, entity_id : int):
    result = db.query(acl_org_model.OrgUser)\
        .filter(acl_org_model.OrgUser.user_id == user_id)\
        .filter(acl_org_model.OrgUser.org_id == org_id)\
        .first()
    if result is not None:
        org_entity_permission_subquery = db.query(acl_org_model.OrgEntityPermission) \
            .filter(acl_org_model.OrgEntityPermission.org_id == org_id) \
            .filter(acl_org_model.OrgEntityPermission.entity_id == source_object_model.Entity.id) \
            .exists()

        user_entity_add_permission_subquery = db.query(acl_user_model.UserEntityAddPermission) \
            .filter(acl_user_model.UserEntityAddPermission.user_id == user_id) \
            .filter(acl_user_model.UserEntityAddPermission.entity_id == source_object_model.Entity.id) \
            .exists()

        user_entity_rev_permission_subquery = ~db.query(acl_user_model.UserEntityRevPermission) \
            .filter(acl_user_model.UserEntityRevPermission.user_id == user_id) \
            .filter(acl_user_model.UserEntityRevPermission.entity_id == source_object_model.Entity.id) \
            .exists()

        result = db.query(source_object_model.Entity, acl_org_model.Org, acl_user_model.User) \
            .filter(source_object_model.Entity.disabled_ts == None) \
            .filter(source_object_model.Entity.id == entity_id) \
            .filter(acl_org_model.Org.id == org_id) \
            .filter(acl_user_model.User.id == user_id) \
            .filter(or_((org_entity_permission_subquery), (user_entity_add_permission_subquery))) \
            .filter(user_entity_rev_permission_subquery) \
            .with_entities(source_object_model.Entity.id)
        for res in result:
            return True
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def is_entities_visible_for_user(db : Session, org_id : int, user_id : int, entity_ids : list[int]):
    result = db.query(acl_org_model.OrgUser)\
        .filter(acl_org_model.OrgUser.user_id == user_id)\
        .filter(acl_org_model.OrgUser.org_id == org_id)\
        .first()
    if result is not None:
        org_entity_permission_subquery = db.query(acl_org_model.OrgEntityPermission) \
            .filter(acl_org_model.OrgEntityPermission.org_id == org_id) \
            .filter(acl_org_model.OrgEntityPermission.entity_id == source_object_model.Entity.id) \
            .exists()

        user_entity_add_permission_subquery = db.query(acl_user_model.UserEntityAddPermission) \
            .filter(acl_user_model.UserEntityAddPermission.user_id == user_id) \
            .filter(acl_user_model.UserEntityAddPermission.entity_id == source_object_model.Entity.id) \
            .exists()

        user_entity_rev_permission_subquery = ~db.query(acl_user_model.UserEntityRevPermission) \
            .filter(acl_user_model.UserEntityRevPermission.user_id == user_id) \
            .filter(acl_user_model.UserEntityRevPermission.entity_id == source_object_model.Entity.id) \
            .exists()

        result = db.query(source_object_model.Entity, acl_org_model.Org, acl_user_model.User) \
            .filter(source_object_model.Entity.disabled_ts == None) \
            .filter(source_object_model.Entity.id.in_(entity_ids)) \
            .filter(acl_org_model.Org.id == org_id) \
            .filter(acl_user_model.User.id == user_id) \
            .filter(or_((org_entity_permission_subquery), (user_entity_add_permission_subquery))) \
            .filter(user_entity_rev_permission_subquery) \
            .with_entities(source_object_model.Entity.id)
        i = 0
        for res in result:
            i = i+1
        if i == len(entity_ids):
            return True
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def add_user(db : Session, user : user_schema.UserCreate):
    db_user = acl_user_model.User(
        email = user.email
    )
    db.add(db_user)
    db.flush()
    db.refresh(db_user)
    return db_user

def get_all(db : Session, org_id : int, skip : int, limit : int):
    results = []

    result = db.query(acl_user_model.User) \
        .join(acl_org_model.OrgUser) \
        .filter(acl_user_model.User.id == acl_org_model.OrgUser.user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
        .offset(skip) \
        .limit(limit) \
        .all()
    for res in result:
        return result
    return results

def delete_user(db : Session, user_id : int):
    db_user = get_user_by_id(db, user_id)
    db_user.disabled_ts = datetime.now()
    return db_user
