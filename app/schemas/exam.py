from pydantic import BaseModel
from datetime import datetime

class ExamSchema(BaseModel):
    contest_id: str
    title: str
    description: str
    is_active: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contest_id": "6698921e0ab511463f14d0a9",
                    "title": "Python Exam",
                    "description": "Python exam for beginners.",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
        }
    }


class UpdateExamSchema(BaseModel):
    contest_id: str
    title: str
    description: str
    is_active: bool
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contest_id": "6698921e0ab511463f14d0a9",
                    "title": "Python Exam",
                    "description": "Python exam for beginners.",
                    "is_active": True,
                    "updated_at": datetime.now()
                }
            ]
        }
    }

