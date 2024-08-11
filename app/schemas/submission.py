from datetime import datetime
from typing import List
from pydantic import BaseModel


class SubmittedProblem(BaseModel):
    problem_id: str
    submitted_code: str | None = None
    submitted_choice: str | None = None

class Submission(BaseModel):
    submitted_problems: List[SubmittedProblem] | None = None
    retake_id: str | None = None
    created_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "submitted_problems": [
                        {
                            "problem_id": "66988270a478a22b8a94a985",
                            "submitted_code": "class Solution:\n    def add_num(a: int, b: int) -> int: \n      return a + b",
                            "submitted_choice": None
                        }
                    ],
                    "retake_id": "66a8b8e5b743acd788da41da",
                    "created_at": datetime.now()
                }
            ]
        }
    }


class SubmittedResult(SubmittedProblem):
    title: str
    description: str
    public_testcases_results: list | None = None
    private_testcases_results: list | None = None
    choice_results: list | None = None
    is_pass_problem: bool = False


class SubmissionDB(BaseModel):
    exam_id: str
    clerk_user_id: str
    retake_id: str | None = None
    submitted_problems: List[SubmittedResult] | None = None
    total_score: int | None = None
    total_problems: int | None = None
    created_at: datetime = datetime.now()


class UpdateSubmissionDB(BaseModel):
    retake_id: str | None = None
    submitted_problems: List[SubmittedResult] | None = None
    total_score: int | None = None
    total_problems: int | None = None
    created_at: datetime = datetime.now()
    
