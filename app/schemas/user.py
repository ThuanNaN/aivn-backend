from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel


class UserSchema(BaseModel):
    clerk_user_id: str 
    email: str 
    username: str 
    role: str 
    avatar: str 
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class UpdateUserInfoSchema(BaseModel):
    username: Optional[str]
    avatar: Optional[str]
    updated_at: datetime = datetime.now()


class UpdateUserRoleSchema(BaseModel):
    role: Optional[str]
    updated_at: datetime = datetime.now()


class WhiteListSchema(BaseModel):
    email: str
    nickname: str


class ResponseModel(BaseModel):
    data: Union[list, dict]
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
    