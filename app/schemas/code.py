from typing import List
from pydantic import BaseModel


class CodeSchema(BaseModel):
    problem_id: str
    code: str


class TestcaseResult(BaseModel):
    testcase_id: str
    input: dict
    output: list | set | dict | str | int | float | bool | None
    is_pass: bool
    error: str | None

class PublicTestcaseResult(TestcaseResult):
    expected_output: list | set | dict | str | int | float | bool | None


class TestedSchema(BaseModel):
    public_testcases_results: List[PublicTestcaseResult]
    private_testcases_results: List[TestcaseResult]
    error: str | None


class ResponseModel(BaseModel):
    data: TestedSchema
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int
