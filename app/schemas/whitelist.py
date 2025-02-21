from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, field_validator
from fastapi import HTTPException


class WhiteListSchema(BaseModel):
    nickname: str
    email: str
    cohort: int = 2024
    is_auditor: bool = False

    @field_validator('email')
    def email_must_not_have_space(cls, email):
        if email != email.lower():
            raise HTTPException(status_code=400, detail="Email must be lower case")
        try:
            emailinfo = validate_email(email, check_deliverability=False)
            email = emailinfo.normalized
        except EmailNotValidError as e:
            raise HTTPException(status_code=400, detail=str(e))
        else:
            return email


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
    