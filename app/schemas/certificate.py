from pydantic import BaseModel
from datetime import datetime

class CertificateSchema(BaseModel):
    clerk_user_id: str
    submission_id: str
    result_score: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "clerk_user_id": "user_2iQK5HNegIsVs2E0ymBAMQDYPO2",
                    "submission_id": "66f3825fc39191c32c071940",
                    "result_score": "800/1000"
                }
            ]
        }
    }
    
class CertificateDB(CertificateSchema):
    validation_id: str
    created_at: datetime


class UpdateCertificateDB(BaseModel):
    result_score: str
    created_at: datetime
