from pydantic import BaseModel
from datetime import datetime, UTC


class ProblemCategory(BaseModel):
    problem_id: str
    category_id: str
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "example": {
                "problem_id": "66988270a478a22b8a94a985",
                "category_id": "6698ada934d6a23fc9673695",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
        }
    }
