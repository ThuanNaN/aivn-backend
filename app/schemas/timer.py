from pydantic import BaseModel
from datetime import datetime


class TimerSchema(BaseModel):
    exam_id: str
    clerk_user_id: str
    start_time: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "exam_id": "6699f5ff1825a0ac6caeaff5",
                    "clerk_user_id": "user_2i6UhSI529yNnyhlrKagEQJ1Fw6",
                    "start_time": datetime.now()
                }
            ]
        }
    }

class TimerSchemaDB(TimerSchema):
    clerk_user_id: str
