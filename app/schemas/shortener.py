from pydantic import BaseModel
from datetime import datetime

class ShortenerSchema(BaseModel):
    original_url: str
    short_url: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_url": "http://localhost:8000/v1/meeting/6785f2305864501ac896eebf",
                    "short_url": "http://localhost:8000/v1/meeting/basic-cnn",
                }
            ]
        }
    }

class ShortenerSchemaDB(ShortenerSchema):
    creator_id: str
    created_at: datetime
    updated_at: datetime
