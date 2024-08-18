from pydantic import BaseModel
from datetime import datetime, UTC


class ExamProblem(BaseModel):
    exam_id: str
    problem_id: str
    index: int
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "example": {
                "exam_id": "6698b45cb077395367734a15",
                "problem_id": "66988270a478a22b8a94a985",
                "index": 0,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
        }
    }

class ExamProblemDB(ExamProblem):
    creator_id: str


class UpdateExamProblem(BaseModel):
    index: int
    creator_id: str
    updated_at: datetime = datetime.now(UTC)
