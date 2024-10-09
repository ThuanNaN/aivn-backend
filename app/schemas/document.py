from pydantic import BaseModel
from datetime import datetime

class DocumentSchema(BaseModel):
    file_name: str
    meeting_id: str
    mask_url: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "file_name": "test_image.jpg",
                    "mask_url": "https://www.google.com/test_image.jpg",
                    "meeting_id": "6698921e0ab511463f14d0a9"
                }
            ]
        }
    }


class DocumentSchemaDB(DocumentSchema):
    creator_id: str
    created_at: datetime
    updated_at: datetime


class UpdateDocumentSchema(BaseModel):
    file_name: str | None = None
    meeting_id: str | None = None
    mask_url: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "file_name": "test_image.png",
                    "mask_url": "https://www.google.com/test_image.png",
                    "meeting_id": "6698921e0ab511463f14d0a9"
                }
            ]
        }
    }

class UpdateDocumentSchemaDB(UpdateDocumentSchema):
    creator_id: str
    updated_at: datetime
