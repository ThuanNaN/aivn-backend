from pydantic import BaseModel
from datetime import datetime


class TimerSchema(BaseModel):
    exam_id: str
    start_time: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "exam_id": "6698b45cb077395367734a15",
                    "start_time": datetime.now()
                }
            ]
        }
    }

class TimerSchemaDB(TimerSchema):
    clerk_user_id: str
