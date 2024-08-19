from pydantic import BaseModel
from datetime import datetime

class ExamSchema(BaseModel):
    contest_id: str
    title: str
    description: str
    is_active: bool
    duration: int

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
                }
            ]
        }
    }

class ExamSchemaDB(ExamSchema):
    creator_id: str
    created_at: datetime
    updated_at: datetime


class UpdateExamSchema(BaseModel):
    contest_id: str
    title: str
    description: str
    is_active: bool
    duration: int

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
                }
            ]
        }
    }

class UpdateExamSchemaDB(UpdateExamSchema):
    creator_id: str
    updated_at: datetime


class OrderSchema(BaseModel):
    problem_id: str
    index: int
