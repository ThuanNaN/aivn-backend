from pydantic import BaseModel
from datetime import datetime


class SettingSchema(BaseModel):
    exam_id: str
    duration: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "exam_id": "1",
                    "duration": 30,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
        }
    }

class UpdateSettingSchema(BaseModel):
    duration: int
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "duration": 50,
                    "updated_at": datetime.now()
                }
            ]
        }
    }
