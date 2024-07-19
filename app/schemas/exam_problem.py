from pydantic import BaseModel
from datetime import datetime


class ExamProblem(BaseModel):
    exam_id: str
    problem_id: str
    index: int = 0
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "example": {
                "exam_id": "6698b45cb077395367734a15",
                "problem_id": "66988270a478a22b8a94a985",
                "index": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
    }

class ExamProblemDB(ExamProblem):
    creator_id: str


class UpdateExamProblem(BaseModel):
    index: int
    updated_at: datetime = datetime.now()


class UpdateExamProblemDB(UpdateExamProblem):
    creator_id: str
