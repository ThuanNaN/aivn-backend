from pydantic import BaseModel
from datetime import datetime, UTC

class ExamSchema(BaseModel):
    contest_id: str
    title: str
    description: str
    is_active: bool
    duration: int
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contest_id": "6698921e0ab511463f14d0a9",
                    "title": "Python Exam",
                    "description": "Python exam for beginners.",
                    "is_active": True,
                    "duration": 60,
                    "is_active": True,
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC)
                }
            ]
        }
    }

class ExamSchemaDB(ExamSchema):
    creator_id: str


class UpdateExamSchema(BaseModel):
    contest_id: str
    title: str
    description: str
    is_active: bool
    duration: int
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contest_id": "6698921e0ab511463f14d0a9",
                    "title": "Python Exam",
                    "is_active": True,
                    "duration": 60,
                    "description": "Python exam for beginners.",
                    "is_active": True,
                    "updated_at": datetime.now(UTC)
                }
            ]
        }
    }

class UpdateExamSchemaDB(UpdateExamSchema):
    creator_id: str


class OrderSchema(BaseModel):
    problem_id: str
    index: int
