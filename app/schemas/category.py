from pydantic import BaseModel
from datetime import datetime, UTC

    
class CategoryModel(BaseModel):
    category_name: str
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": "python",
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC)
                }
            ]
        }
    }


class UpdateCategorySchema(BaseModel):
    category_name: str
    updated_at: datetime = datetime.now(UTC)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": "pytorch",
                    "updated_at": datetime.now(UTC)
                }
            ]
        }
    }
