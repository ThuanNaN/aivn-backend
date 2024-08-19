from pydantic import BaseModel
from datetime import datetime


class ExamProblem(BaseModel):
    exam_id: str
    problem_id: str
    index: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "exam_id": "6698b45cb077395367734a15",
                "problem_id": "66988270a478a22b8a94a985",
                "index": 0,
            }
        }
    }

class ExamProblemDB(ExamProblem):
    creator_id: str
    created_at: datetime
    updated_at: datetime

class UpdateExamProblem(BaseModel):
    index: int
    creator_id: str

class UpdateExamProblemDB(UpdateExamProblem):
    updated_at: datetime