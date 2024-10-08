from pydantic import BaseModel
from datetime import datetime

class MeetingSchema(BaseModel):
    title: str
    description: str
    lecturer: str
    date: str  # isoformat
    start_time: str # isoformat
    end_time: str # isoformat
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Pytorch Basics",
                    "description": "This is a basic course about Pytorch",
                    "lecturer": "Dr.Dinh Vinh",
                    "date": "2024-10-08T01:45:21.527550",
                    "start_time": "2024-10-08T01:47:24.432219",
                    "end_time": "2024-10-08T01:47:34.334284"
                }
            ]
        }
    }

class MeetingSchemaDB(BaseModel):
    title: str
    description: str
    lecturer: str
    date: datetime
    start_time: datetime
    end_time: datetime
    creator_id: str
    created_at: datetime
    updated_at: datetime


class UpdateMeetingSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    lecturer: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Pytorch Basics",
                    "description": "This is a basic course about Pytorch",
                    "lecturer": "Dr.Quang Vinh",
                    "date": "2024-10-08T01:45:21.527550",
                    "start_time": "2024-10-08T01:47:24.432219",
                    "end_time": "2024-10-08T01:47:34.334284"
                }
            ]
        }
    }


class UpdateMeetingSchemaDB(BaseModel):
    title: str | None = None
    description: str | None = None
    lecturer: str | None = None
    date: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    creator_id: str
    created_at: datetime
    updated_at: datetime
