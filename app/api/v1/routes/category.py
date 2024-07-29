from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.api.v1.controllers.category import (
    add_category,
    retrieve_categories,
    retrieve_category,
    update_category
)
from app.schemas.category import (
    CategoryModel,
    UpdateCategorySchema
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
async def create_category(category: CategoryModel):
    category_dict = category.model_dump()
    new_category = await add_category(category_dict)
    return DictResponseModel(data=new_category,
                             message="Category created successfully.",
                             code=status.HTTP_200_OK)


@router.get("/categories",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all categories")
async def get_categories():
    categories = await retrieve_categories()
    if categories:
        return ListResponseModel(data=categories,
                                 message="Categories retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Occur error when retrieve categories.", 
        message="Categories not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a category with a matching ID")
async def get_category(id: str):
    category = await retrieve_category(id)
    if category:
        return DictResponseModel(data=category,
                                 message="Category retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Occur error when retrieve category.",
        message="Category not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.patch("/{id}",
              dependencies=[Depends(is_admin)],
              description="Update a category with a matching ID")
async def update_category_data(id: str, category: UpdateCategorySchema):
    category_dict = category.model_dump()
    updated_category = await update_category(id, category_dict)
    if updated_category:
        return ListResponseModel(data=[],
                                 message="Category updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Occur error when update category.",
        message="Category not found.",
                              code=status.HTTP_404_NOT_FOUND)