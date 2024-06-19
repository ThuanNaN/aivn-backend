from datetime import datetime
from pydantic import BaseModel



class SubmissionSchema(BaseModel):
    user_id: str
    problem_id: str
    code: str
    created_at: datetime = datetime.now().isoformat()


class UpdateSubmissionSchema(BaseModel):
    pass


class ResponseModel(BaseModel):
    data: list
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
