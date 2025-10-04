from fastapi import Request
import logging

logger = logging.getLogger(__name__)
PREFIX = 'Bearer '
def get_token(header):
    if not header.startswith(PREFIX):
        logger.error("Authorization header does not start with Bearer")
        raise ValueError('Invalid token')

    return header[len(PREFIX):]

def get_auth_token(request: Request):
    return get_token(request.headers["Authorization"])