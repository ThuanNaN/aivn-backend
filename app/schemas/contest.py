from typing import List
from pydantic import BaseModel
from datetime import datetime
from .enum_category import CertificateEnum

class ContestSchema(BaseModel):
    title: str = "Contest"
    description: str = "Description of the contest."
    instruction: str = "Details and instruction for the contest."
    is_active: bool = False
    cohorts: List[int] | None = None
    certificate_template: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Python Contest",
                    "description": "Python contest for beginners.",
                    "instruction": "Details and instruction for the contest.",
                    "is_active": True,
                    "cohorts": [2024],
                    "certificate_template": CertificateEnum.FOUNDATION.value
                }
            ]
        }
    }

class ContestSchemaDB(ContestSchema):
    creator_id: str
    slug: str = "auto-gen-from-title"
    created_at: datetime
    updated_at: datetime


class UpdateContestSchema(BaseModel):
    title: str | None = None
    instruction: str | None = None
    description: str | None = None
    is_active: bool | None = None
    cohorts: List[int] | None = None
    certificate_template: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Python Contest",
                    "description": "Python contest for beginners.",
                    "instruction": "Details and instruction for the contest.",
                    "is_active": True,
                    "cohorts": [2024, 2025],
                    "certificate_template": CertificateEnum.FOUNDATION.value
                }
            ]
        }
    }

class UpdateContestSchemaDB(UpdateContestSchema):
    creator_id: str
    slug: str = "auto-gen-from-title"
    updated_at: datetime
