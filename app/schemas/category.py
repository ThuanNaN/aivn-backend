from pydantic import BaseModel
from datetime import datetime, UTC

    
class CategorySchema(BaseModel):
    category_name: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": "python",
                }
            ]
        }
    }


class CategorySchemaDB(CategorySchema):
    created_at: datetime
    updated_at: datetime

class UpdateCategorySchema(BaseModel):
    category_name: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": "pytorch",
                }
            ]
        }
    }

class UpdateCategorySchemaDB(UpdateCategorySchema):
    updated_at: datetime
