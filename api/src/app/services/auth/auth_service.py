from app.services import config_service, exception_service
import boto3
import base64
def getToken(token: str):
    app_client_id = config_service.app_client_id
    user_pool_id = config_service.user_pool_id

    client = boto3.client("cognito-idp", region_name="us-east-1")

    try:
        if not token or not isinstance(token, str):
            raise ValueError("Invalid token format")
        
        decoded_bytes = base64.b64decode(token)
        decoded_string = decoded_bytes.decode('utf-8')
        
        if ':' not in decoded_string:
            raise ValueError("Invalid credential format")
        
        credentials = decoded_string.split(':', 1)
        if len(credentials) != 2:
            raise ValueError("Invalid credential format")
        
        username, password = credentials
        
        if not username or not password:
            raise ValueError("Username and password cannot be empty")
            
    except (base64.binascii.Error, UnicodeDecodeError, ValueError) as e:
        raise exception_service.AccessDeniedException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="Invalid authentication credentials format",
                                          type="invalid.credentials",
                                          loc=[])],
                exception_service.Ctx("")
            )
        )

    response = client.admin_initiate_auth(
        UserPoolId=user_pool_id,
        ClientId=app_client_id,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password
        }
    )
    if "AuthenticationResult" in response and "IdToken" in response["AuthenticationResult"]:
        accessToken = response["AuthenticationResult"]["IdToken"]
        return {"access_token": accessToken}
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op",
                                      type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

