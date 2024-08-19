from pydantic import BaseModel
from datetime import datetime

class ContestSchema(BaseModel):
    title: str
    description: str
    is_active: bool


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Python Contest",
                    "description": "Python contest for beginners.",
                    "is_active": True,
                }
            ]
        }
    }

class ContestSchemaDB(ContestSchema):
    creator_id: str
    created_at: datetime
    updated_at: datetime

class UpdateContestSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Python Contest",
                    "description": "Python contest for beginners.",
                    "is_active": True,
                }
            ]
        }
    }

class UpdateContestSchemaDB(UpdateContestSchema):
    creator_id: str
    updated_at: datetime
