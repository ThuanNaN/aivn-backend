from datetime import datetime
from typing import List
from pydantic import BaseModel


class ProblemSubmission(BaseModel):
    problem_id: str
    code: str


class SubmissionSchema(BaseModel):
    user_id: str
    problems: List[ProblemSubmission]
    created_at: datetime = datetime.now().isoformat()


class ResponseModel(BaseModel):
    data: dict
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
