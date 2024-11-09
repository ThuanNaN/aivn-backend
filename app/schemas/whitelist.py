from datetime import datetime
from pydantic import BaseModel, field_validator


class WhiteListSchema(BaseModel):
    email: str
    nickname: str

    @field_validator('email')
    def email_must_be_lower(cls, v):
        if v != v.lower():
            raise ValueError('Email must be in lowercase')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "abc123@gmail.com",
                "nickname": "abc123",
            }
        }
    }

class WhiteListSchemaDB(WhiteListSchema):
    created_at : datetime
    updated_at : datetime


class UpdateWhiteList(BaseModel):
    nickname: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "nickname": "Abc123",
            }
        }
    }


class UpdateWhiteListDB(UpdateWhiteList):
    updated_at : datetime
    