from typing import List
from pydantic import BaseModel, field_validator
from datetime import datetime

class MeetingSchema(BaseModel):
    title: str
    description: str
    lecturer: str
    date: str  # isoformat
    start_time: str # isoformat
    end_time: str # isoformat
    document_data: list[dict] | None = None
    join_link: str | None = None
    cohorts: List[int] | None = [2024]

    @field_validator("cohorts", mode="before")
    def validate_cohorts(cls, v):
        if v is None or v == []:
            return [2024]
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Pytorch Basics",
                    "description": "This is a basic course about Pytorch",
                    "lecturer": "Dr.Dinh Vinh",
                    "cohorts": [2024],
                    "date": "2024-10-08T01:45:21.527550",
                    "start_time": "2024-10-08T01:47:24.432219",
                    "end_time": "2024-10-08T01:47:34.334284",
                    "document_data": [
                        {
                            "file_name": "test_image.jpg",
                            "mask_url": "https://www.google.com/test_image.jpg",
                            "meeting_id": "6698921e0ab511463f14d0a9"
                        }
                    ],
                    "join_link": "https://meet.google.com/aivn123",
                    "record": "https://www.youtube.com/watch?v=w1NlIsgClLo&t=4971s"
                }
            ]
        }
    }

class MeetingSchemaDB(BaseModel):
    title: str
    description: str
    lecturer: str
    cohorts: List[int] = [2024]
    date: datetime
    start_time: datetime
    end_time: datetime
    creator_id: str
    join_link: str | None = None
    slug: str
    record: str | None = None
    created_at: datetime
    updated_at: datetime


class UpdateMeetingSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    lecturer: str | None = None
    cohorts: List[int] | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    document_data: list[dict] | None = None
    join_link: str | None = None
    record: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Pytorch Basics",
                    "description": "This is a basic course about Pytorch",
                    "lecturer": "Dr.Quang Vinh",
                    "cohorts": [2024, 2025],
                    "date": "2024-10-08T01:45:21.527550",
                    "start_time": "2024-10-08T01:47:24.432219",
                    "end_time": "2024-10-08T01:47:34.334284",
                    "document_data": [
                        {
                            "file_name": "test_image.jpg",
                            "mask_url": "https://www.google.com/test_image.jpg",
                            "meeting_id": "6698921e0ab511463f14d0a9"
                        }
                    ],
                    "record": "https://www.youtube.com/watch?v=w1NlIsgClLo&t=4971s"
                }
            ]
        }
    }

class UpdateMeetingSchemaDB(BaseModel):
    title: str | None = None
    description: str | None = None
    lecturer: str | None = None
    cohorts: List[int] | None = None
    date: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    creator_id: str
    join_link: str | None = None
    slug: str | None = None
    record: str | None = None
    created_at: datetime
    updated_at: datetime
