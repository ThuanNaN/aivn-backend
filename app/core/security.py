import jwt
from jwt.exceptions import (
    ExpiredSignatureError, 
    ImmatureSignatureError, 
    InvalidTokenError
)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.config import settings
from app.api.v1.controllers.user import retrieve_user


if settings.ENV_TYPE == "development":
    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvZrZXYBd+sjK1wQ3t2yH
QdhRL8gOGJrgkuNqW30dRmWShRQ6/UCybp1ojgJKW3P31o8fLhuOCnKCjAjDPI0X
QbtjajAKcoCUEcx38VHLv2gT5STIhgvSC9IrDEOflmFz6+5KbQQcQBvyV51V9eb7
FaeGRe9CIRlMiO+tKXqmx3Lt0Vnw+5GuvLV5/nWQspElpn1pYRMYmI0lh6/KFLQ0
PaYSLZenUk1UfGiLbgVcuv9Aht1n7wdb2SmGgIcTVqhYnUGNzsXKCglRZ7A6bH1n
pklFqYoNwF4Mps7hKQ1D/ddxAGEaASNwMam5pMt2ZeOohOmX5BNQ7YuGzyjf+KZD
ywIDAQAB
-----END PUBLIC KEY-----
"""

elif settings.ENV_TYPE == "production":
    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsZ/vvCETUyrlqfnKpCfN
fZhOrColBWz3rpjBSf3zDuZm5APCVUdI19ETgPPxKJBRaa8s9ij0BrIIFDU3ARnd
fonsWZpxbdFG3wfWOPj+rRMDVcxpcWnhkdIHUKO/AiJqb9+nsCDa29njW3Co+O4u
pK2bN5grHSziLUbCIjLf7jmtVdbmXqyd3Y+OdSj1dwjzrb54AIe/4xNUHS6KSU9x
Du0rTgnA0me4MUuL72aHx0OxSDfxGnWqFe+HETQnDuCLCY2R5kd99H9tKfbKWsK6
E40n+U5RdI14aGIkhfcKE7qeY7Je+t0L6z/ghNtVsEI/C0vwNGTYp04JVcu+JV14
pQIDAQAB
-----END PUBLIC KEY-----
"""

else:
    raise ValueError("Invalid ENV_TYPE")

ALGORITHM = "RS256"
oauth2_scheme = HTTPBearer()


async def is_authenticated(oauth2_scheme: HTTPBearer = Depends(oauth2_scheme)):
    try:
        token = oauth2_scheme.credentials
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        clerk_user_id: str = payload.get("sub")
        return clerk_user_id
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ImmatureSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not yet valid (iat)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def is_admin(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough permissions",
        )
    return user

async def is_aio(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user["role"] not in ["admin", "aio"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough permissions",
        )
    return user
