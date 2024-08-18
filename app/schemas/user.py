from typing import Optional, Literal
from datetime import datetime, UTC
from pydantic import BaseModel


class UserSchema(BaseModel):
    clerk_user_id: str 
    email: str 
    username: str 
    role: str 
    avatar: str 
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "example": {
                "clerk_user_id": "1",
                "email": "example@gmail.com",
                "username": "example",
                "role": "user",
                "avatar": "example.jpg",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
        }
    }


class UpdateUserSchema(BaseModel):
    role: Optional[Literal["user", "aio", "admin"]] 
    updated_at: datetime = datetime.now(UTC)


# class UpdateUserInfoSchema(BaseModel):
#     username: Optional[str]
#     avatar: Optional[str]
#     updated_at: datetime = datetime.now(UTC)


class UpdateUserRoleSchema(BaseModel):
    role: Optional[str]
    updated_at: datetime = datetime.now(UTC)


class WhiteListSchema(BaseModel):
    email: str
    nickname: str