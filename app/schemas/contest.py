from pydantic import BaseModel
from datetime import datetime


class ContestSchema(BaseModel):
    title: str
    description: str
    is_active: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Python Contest",
                    "description": "Python contest for beginners.",
                    "is_active": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
        }
    }

class ContestSchemaDB(ContestSchema):
    creator_id: str


class UpdateContestSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Python Contest",
                    "description": "Python contest for beginners.",
                    "is_active": True,
                    "updated_at": datetime.now()
                }
            ]
        }
    }

class UpdateContestSchemaDB(UpdateContestSchema):
    creator_id: str
