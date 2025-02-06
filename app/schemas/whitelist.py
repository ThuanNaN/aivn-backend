from datetime import datetime
from pydantic import BaseModel, field_validator


class WhiteListSchema(BaseModel):
    nickname: str
    email: str
    cohort: int = 2024
    is_auditor: bool = False

    @field_validator('email')
    def email_must_be_lower(cls, v):
        if v != v.lower():
            raise ValueError('Email must be in lowercase')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "nickname": "abc123",
                "email": "abc123@gmail.com",
                "cohort": "2024",
                "is_auditor": False,
            }
        }
    }

class WhiteListSchemaDB(WhiteListSchema):
    created_at : datetime
    updated_at : datetime


class UpdateWhiteList(BaseModel):
    nickname: str | None = None
    cohort: int | None = None
    is_auditor: bool | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "nickname": "Abc123",
                "cohort": "2025",
                "is_auditor": True,
            }
        }
    }


class UpdateWhiteListDB(UpdateWhiteList):
    updated_at : datetime
    