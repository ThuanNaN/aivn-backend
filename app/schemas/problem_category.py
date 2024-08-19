from pydantic import BaseModel
from datetime import datetime, UTC


class ProblemCategory(BaseModel):
    problem_id: str
    category_id: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "problem_id": "66988270a478a22b8a94a985",
                "category_id": "6698ada934d6a23fc9673695",
            }
        }
    }

class ProblemCategoryDB(ProblemCategory):
    created_at: datetime
    updated_at: datetime