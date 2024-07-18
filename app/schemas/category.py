from pydantic import BaseModel
from datetime import datetime

    
class CategoryModel(BaseModel):
    category_name: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": "python",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
        }
    }


class UpdateCategorySchema(BaseModel):
    category_name: str
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": "pytorch",
                    "updated_at": datetime.now()
                }
            ]
        }
    }
