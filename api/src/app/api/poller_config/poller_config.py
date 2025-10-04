from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.model.pydantic.source_objects import poller_config_schema
from app.services import poller_config_service
from app.services.acl import app_user_service
from app.services.secrets_service import SecretsService
from app.services import config_service
import os

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import auth_service

# def verify_token(request: Request):
#     if "Authorization" in request.headers:
#         print("Authorization header found...")
#         auth_header = request.headers["Authorization"]
#         print("Auth header: ", auth_header)
#         if auth_header.startswith("Bearer ") and len(auth_header) > 7:
#             token = auth_header[7:]
#             print("Token: ", token)
#             auth_service.verify_token(token)
#             return token
#     raise HTTPException(status_code=403, detail="Invalid or missing token")

def init(app, get_db):
    @app.get("/org/{org_id}/poller", response_model=List[poller_config_schema.PollerConfig])
    def read_org_poller_configs(
        request: Request,
        org_id: int, 
        db: Session = Depends(get_db)
    ):
        # verify_token(request)
        user_id = request.state.user_id
        if app_user_service.is_user_app_admin(db, user_id):
            configs = poller_config_service.get_poller_configs_by_org(db, org_id)
            return configs

    @app.get("/poller/{poller_id}", response_model=poller_config_schema.PollerConfig)
    def read_poller_config(
        request: Request,
        poller_id: int, 
        db: Session = Depends(get_db)
    ):
        # verify_token(request)
        user_id = request.state.user_id
        if app_user_service.is_user_app_admin(db, user_id):
            config = poller_config_service.get_poller_config_by_poller_id(db, poller_id)
            if config is None:
                raise HTTPException(status_code=404, detail="Poller config not found")
            return config

    @app.get("/poller", response_model=List[poller_config_schema.PollerConfig])
    def read_poller_configs_by_type(
        request: Request,
        type: str, 
        db: Session = Depends(get_db)
    ):
        # verify_token(request)
        user_id = request.state.user_id
        if app_user_service.is_user_app_admin(db, user_id):
            configs = poller_config_service.get_poller_configs_by_type(db, type)
            return configs

    @app.post("/poller", response_model=poller_config_schema.PollerConfig)
    def create_org_poller_config(
        request: Request,
        config: poller_config_schema.PollerConfigCreate,
        db: Session = Depends(get_db)
    ):
        # verify_token(request)
        user_id = request.state.user_id
        if app_user_service.is_user_app_admin(db, user_id):
            # Initialize secrets service
            aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            secrets_service = SecretsService(aws_access_key_id, aws_secret_access_key)
            
            # Get encryption key and encrypt the config
            encryption_key = secrets_service.get_encryption_key()
            encrypted_config = secrets_service.encrypt_config(config.config, encryption_key)
            
            # Create a new config object with encrypted config
            encrypted_config_create = poller_config_schema.PollerConfigCreate(
                org_id=config.org_id,
                poller_type=config.poller_type,
                poller_name=config.poller_name,
                config=encrypted_config,
                status=config.status
            )
            
            return poller_config_service.create_poller_config(db, encrypted_config_create)