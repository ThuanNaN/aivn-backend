from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class CategoryEnum(Enum):
    PYTHON = "python"
    NUMPY = "numpy"
    PYTORCH = "pytorch"

    @classmethod
    def get_list(cls) -> list[str]:
        return [category.value for category in cls]
    
class CategoryModel(BaseModel):
    category_name: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_name": CategoryEnum.PYTHON.value,
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
                    "category_name": CategoryEnum.PYTHON.value,
                    "updated_at": datetime.now()
                }
            ]
        }
    }
