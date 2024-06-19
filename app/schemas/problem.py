from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class TestCase(BaseModel):
    input: str
    expected_output: str


class ProblemSchema(BaseModel):
    title: str
    description: str
    index: int
    slug: str
    code_template: str
    public_testcases: List[TestCase]
    private_testcases: List[TestCase]
    created_at: datetime = datetime.now().isoformat()
    updated_at: datetime = datetime.now().isoformat()


class UpdateProblemSchema(BaseModel):
    title: Optional[str]
    description: Optional[str]
    index: Optional[int]
    slug: Optional[str]
    code_template: Optional[str]
    public_testcases: Optional[List[TestCase]]
    private_testcases: Optional[List[TestCase]]
    updated_at: datetime = datetime.now().isoformat()


class ResponseModel(BaseModel):
    data: list
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int