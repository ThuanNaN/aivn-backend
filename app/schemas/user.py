from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel


class UserSchema(BaseModel):
    clerk_user_id: str | None = None
    email: str | None = None
    username: str | None = None
    role: str | None = None
    avatar: str | None = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class UpdateUserSchema(BaseModel):
    username: Optional[str]
    role: Optional[str]
    avatar: Optional[str]
    updated_at: datetime = datetime.now()


class ResponseModel(BaseModel):
    data: Union[list, dict]
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
    