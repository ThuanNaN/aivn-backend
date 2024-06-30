from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class TestCase(BaseModel):
    testcase_id: UUID = Field(default_factory=uuid4)
    input: str | None
    expected_output: str | None


class Choice(BaseModel):
    choice_id: UUID = Field(default_factory=uuid4)
    answer: str | None
    is_correct: bool | None


class ProblemSchema(BaseModel):
    title: str
    description: str
    index: int
    slug: str
    
    # >>> code problems
    code_template: str | None
    public_testcases: List[TestCase] | None = None
    private_testcases:  List[TestCase] | None = None
    # >>> code problems

    # >>> choice problems
    choices: List[Choice] | None = None
    # >>> choice problems

    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class UpdateProblemSchema(BaseModel):
    title: Optional[str]
    description: Optional[str]
    index: Optional[int]
    slug: Optional[str]
    code_template: Optional[str]
    public_testcases: Optional[List[TestCase]]
    private_testcases: Optional[List[TestCase]]
    choices: Optional[List[Choice]]
    updated_at: datetime = datetime.now()


class OrderSchema(BaseModel):
    problem_id: str
    index: int


class ResponseModel(BaseModel):
    data: List[dict] | dict
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int