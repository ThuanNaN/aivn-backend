from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel


class UserSchema(BaseModel):
    clerk_user_id: str 
    email: str 
    username: str 
    role: str 
    avatar: str 

    model_config = {
        "json_schema_extra": {
            "example": {
                "clerk_user_id": "1",
                "email": "example@gmail.com",
                "username": "example",
                "role": "user",
                "avatar": "example.jpg",
            }
        }
    }


class UserSchemaDB(UserSchema):
    created_at : datetime
    updated_at : datetime


class UpdateUserSchema(BaseModel):
    role: Optional[Literal["user", "aio", "admin"]] 


class UpdateUserSchemaDB(UpdateUserSchema):
    updated_at : datetime


# class UpdateUserInfoSchema(BaseModel):
#     username: Optional[str]
#     avatar: Optional[str]


class WhiteListSchema(BaseModel):
    email: str
    nickname: str