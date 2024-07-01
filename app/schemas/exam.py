from pydantic import BaseModel
from datetime import datetime


class DoExamSchema(BaseModel):
    user_id: str
    start_time: datetime = datetime.now()


class ResponseModel(BaseModel):
    data: dict
    message: str
    code: int

class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int