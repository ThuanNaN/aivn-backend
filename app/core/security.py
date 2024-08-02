import jwt
from jwt.exceptions import (
    ExpiredSignatureError, 
    ImmatureSignatureError, 
    InvalidTokenError
)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.api.v1.controllers.user import retrieve_user

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
