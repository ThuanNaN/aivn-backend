from pydantic import BaseModel
from datetime import datetime
from .enum_category import CertificateEnum

class CertificateSchema(BaseModel):
    clerk_user_id: str
    submission_id: str
    result_score: str
    template: str 

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "clerk_user_id": "user_2iQK5HNegIsVs2E0ymBAMQDYPO2",
                    "submission_id": "66f3825fc39191c32c071940",
                    "result_score": "800/1000",
                    "template": CertificateEnum.FOUNDATION.value
                }
            ]
        }
    }
    
class CertificateDB(CertificateSchema):
    validation_id: str
    created_at: str
