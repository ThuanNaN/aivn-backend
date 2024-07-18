from datetime import datetime
from typing import List
from pydantic import BaseModel


class Problem(BaseModel):
    problem_id: str
    submitted_code: str | None = None
    submitted_choice: str | None = None

class ProblemResult(Problem):
    title: str
    description: str
    public_testcases_results: list | None
    private_testcases_results: list | None
    choice_results: dict | None
    is_pass_problem: bool

class SubmissionSchema(BaseModel):
    exam_id: str
    problems: List[Problem]
    created_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "exam_id": "6698b45cb077395367734a15",
                    "problems": [
                        {
                            "problem_id": "66988270a478a22b8a94a985",
                            "submitted_code": "class Solution:\n    def add_num(a: int, b: int) -> int: \n      return a + b",
                            "submitted_choice": None
                        }
                    ],
                    "created_at": datetime.now()
                }
            ]
        }
    
    }

class SubmissionSchemaDB(SubmissionSchema):
    clerk_user_id: str
    problems: List[ProblemResult]



