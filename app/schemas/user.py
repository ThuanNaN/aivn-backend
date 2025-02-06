from typing import Literal, List
from datetime import datetime
from pydantic import BaseModel


class UserSchema(BaseModel):
    clerk_user_id: str 
    email: str 
    username: str 
    role: str
    cohort: int
    avatar: str
    fullname: str | None = ""
    bio: str | None = ""
    attend_id: str | None = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "clerk_user_id": "1",
                "email": "example@gmail.com",
                "username": "example",
                "role": "user",
                "cohort": 2024,
                "avatar": "example.jpg",
            }
        }
    }


class UserSchemaDB(UserSchema):
    created_at : datetime
    updated_at : datetime


class UpdateUserRole(BaseModel):
    role: Literal["user", "aio", "admin"] | None = None


class UpdateUserRoleDB(UpdateUserRole):
    cohort: int | None = 0
    feasible_cohort: List[int]
    updated_at : datetime


class UpdateUserInfo(BaseModel):
    avatar: str | None = ""
    fullname: str | None = ""
    bio: str | None = "" 

class UpdateUserInfoDB(UpdateUserInfo):
    updated_at : datetime
