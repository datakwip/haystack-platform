import boto3
import json
import base64
from cryptography.fernet import Fernet
from botocore.exceptions import ClientError
from app.services import logger_service
from typing import Optional

logger = logger_service.logger()

class SecretsService:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str = "us-east-1"):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self._encryption_key_cache = None

    def get_encryption_key(self) -> str:
        """Fetch the encryption key from AWS Secrets Manager (with optional caching)."""
        if self._encryption_key_cache:
            return self._encryption_key_cache
        secret_name = "prod/poller_config"
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            logger.error(f"Error getting secret: {str(e)}")
            raise
        else:
            if 'SecretString' in get_secret_value_response:
                secret = json.loads(get_secret_value_response['SecretString'])
                self._encryption_key_cache = secret['encryption_key']
                return self._encryption_key_cache
        logger.error("Encryption key not found in secret.")
        raise ValueError("Encryption key not found in secret.")

    def decrypt_config(self, encrypted_config: str, key: str) -> dict:
        """Decrypt an encrypted config string using the provided key."""
        f = Fernet(key.encode())
        encrypted_bytes = base64.b64decode(encrypted_config.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return json.loads(decrypted_data.decode())

    def encrypt_config(self, config_dict: dict, key: str) -> str:
        """Encrypt a config dictionary using the provided key."""
        f = Fernet(key.encode())
        config_json = json.dumps(config_dict)
        encrypted_bytes = f.encrypt(config_json.encode())
        return base64.b64encode(encrypted_bytes).decode()

    def encrypt_string(self, plain_text: str, key: str) -> str:
        """Encrypt a plain text string using the provided key."""
        f = Fernet(key.encode())
        encrypted_bytes = f.encrypt(plain_text.encode())
        return base64.b64encode(encrypted_bytes).decode()