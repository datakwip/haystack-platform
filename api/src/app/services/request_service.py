from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)
PREFIX = 'Bearer '
def get_token(header):
    if not header.startswith(PREFIX):
        logger.error("Authorization header does not start with Bearer")
        raise ValueError('Invalid token')

    return header[len(PREFIX):]

def get_auth_token(request: Request):
    """
    Extract and validate the Authorization header from the request.

    Returns the token string if valid.
    Raises HTTPException(401) if Authorization header is missing.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    return get_token(auth_header)