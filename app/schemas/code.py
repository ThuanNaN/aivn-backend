from typing import List
from pydantic import BaseModel


class CodeSchema(BaseModel):
    problem_id: str
    code: str


class TestcaseResult(BaseModel):
    testcase_id: str
    is_pass: bool


class TestedSchema(BaseModel):
    public_testcases_results: List[TestcaseResult]
    private_testcases_results: List[TestcaseResult]


class ResponseModel(BaseModel):
    data: TestedSchema
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
