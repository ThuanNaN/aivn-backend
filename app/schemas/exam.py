from pydantic import BaseModel
from datetime import datetime


class DoExamSchema(BaseModel):
    start_time: datetime = datetime.now()

class DoExamDBSchema(DoExamSchema):
    user_id: str


class ResponseModel(BaseModel):
    data: dict
    message: str
    code: int

class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int