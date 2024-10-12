from pydantic import BaseModel
from datetime import datetime

class AttendeeIDSchema(BaseModel):
    attend_id: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "attend_id": "6698921e0ab511463f14d0a9",
                }
            ]
        }
    }

class AttendeeEmailSchema(BaseModel):
    email: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "duongthuan1445@gmail.com",
                }
            ]
        }
    }

class AttendeeSchemaDB(AttendeeIDSchema):
    meeting_id: str
    created_at: datetime
    updated_at: datetime

