from app.utils.logger import Logger
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, status
from app.api.v1.controllers.category import (
    add_category,
    retrieve_categories,
    retrieve_category,
    update_category
)
from app.schemas.category import (
    CategorySchema,
    CategorySchemaDB,
    UpdateCategorySchema,
    UpdateCategorySchemaDB
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated

router = APIRouter()
logger = Logger("routes/category", log_file="category.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Create a new category")
async def create_category(category: CategorySchema):
    category_db = CategorySchemaDB(
        **category.model_dump(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    new_category = await add_category(category_db)
    if isinstance(new_category, Exception):
        return ErrorResponseModel(error=str(new_category),
                                  message="Occur error when create category.",
                                  code=status.HTTP_400_BAD_REQUEST)
    return DictResponseModel(data=new_category,
                             message="Category created successfully.",
                             code=status.HTTP_200_OK)


@router.get("/categories",
            description="Retrieve all categories")
async def get_categories():
    categories = await retrieve_categories()
    if isinstance(categories, Exception):
        return ErrorResponseModel(error=str(categories),
                                  message="Occur error when retrieve categories.",
                                  code=status.HTTP_400_BAD_REQUEST)
    return ListResponseModel(data=categories,
                             message="Categories retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}",
            description="Retrieve a category with a matching ID")
async def get_category(id: str):
    category = await retrieve_category(id)
    if isinstance(category, Exception):
        return ErrorResponseModel(error=str(category),
                                  message="Occur error when retrieve category.",
                                  code=status.HTTP_400_BAD_REQUEST)
    return DictResponseModel(data=category,
                             message="Category retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.patch("/{id}",
              dependencies=[Depends(is_admin)],
              description="Update a category with a matching ID")
async def update_category_data(id: str, category: UpdateCategorySchema):
    category_db = UpdateCategorySchemaDB(
        **category.model_dump(),
        updated_at=datetime.now(UTC)
    )
    update_result = await update_category(id, category_db)
    if isinstance(update_result, Exception):
        return ErrorResponseModel(error=str(update_result),
                                  message="Occur error when update category.",
                                  code=status.HTTP_400_BAD_REQUEST)

    if not update_result:
        return ErrorResponseModel(error="No documents were updated.",
                                  message="Category update failed.",
                                  code=status.HTTP_404_NOT_FOUND)

    return ListResponseModel(data=[],
                             message="Category updated successfully.",
                             code=status.HTTP_200_OK)
