from datetime import datetime
from typing import List
from pydantic import BaseModel

## >> Input schemas
class ProblemSubmission(BaseModel):
    problem_id: str
    submitted_code: str | None = None
    submitted_choice: str | None = None


class SubmissionSchema(BaseModel):
    user_id: str
    problems: List[ProblemSubmission]
    created_at: datetime = datetime.now()
## >> Input schemas


## >> Database schemas
class ProblemSubmissionDB(BaseModel):
    problem_id: str
    submitted_code: str | None = None
    submitted_choice: str | None = None
    title: str
    description: str
    public_testcases_results: list | None = None
    private_testcases_results: list | None = None
    choice_results: list | None = None
    is_pass_problem: bool

class SubmissionDBSchema(BaseModel):
    user_id: str
    problems: List[ProblemSubmissionDB]
    created_at: datetime = datetime.now()
## >> Database schemas


class ResponseModel(BaseModel):
    data: list | dict
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
