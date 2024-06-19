from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    email: str
    created_at: datetime = datetime.now().isoformat()
    updated_at: datetime = datetime.now().isoformat()


class UpdateUserSchema(BaseModel):
    username: Optional[str]
    email: Optional[str]
    updated_at: datetime = datetime.now().isoformat()


class ResponseModel(BaseModel):
    data: list
    message: str
    code: int

class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
    