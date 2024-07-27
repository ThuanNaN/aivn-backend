from typing import Optional, List
from app.utils.logger import Logger
from fastapi import APIRouter, Body, Depends, Query, status
from bson.objectid import ObjectId
from app.api.v1.controllers.problem import (
    add_problem,
    retrieve_problem,
    update_problem,
    delete_problem,
    retrieve_search_filter_pagination,
)
from app.api.v1.controllers.problem_category import (
    add_problem_category,
    add_more_problem_category,
    retrieve_by_problem_category_id,
    retrieve_by_categories,
    delete_problem_category,
    delete_all_by_problem_id
)
from app.schemas.problem import (
    ProblemSchema,
    ProblemSchemaDB,
    UpdateProblemSchema,
    UpdateProblemSchemaDB
)
from app.schemas.problem_category import (
    ProblemCategory
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated
from app.api.v1.controllers.user import retrieve_user

router = APIRouter()
logger = Logger("routes/problem", log_file="problem.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new problem")
async def create_problem(problem: ProblemSchema, user_clerk_id: str = Depends(is_authenticated)):
    problem_dict = problem.model_dump()
    category_ids = problem_dict.pop("category_ids", [])

    problem_db = ProblemSchemaDB(
        **problem_dict,
        creator_id=user_clerk_id
    )
    new_problem = await add_problem(problem_db.model_dump())

    new_problem_categories = []
    if len(category_ids) > 0:
        problem_categories: List[dict] = [
            ProblemCategory(problem_id=new_problem["id"],
                            category_id=category_id).model_dump()
            for category_id in category_ids
        ]
        new_problem_categories = await add_more_problem_category(problem_categories)
        if not new_problem_categories:
            return ErrorResponseModel(error="An error occurred.",
                                      message="Problem-Category was not added.",
                                      code=status.HTTP_404_NOT_FOUND)

    new_problem["categories"] = new_problem_categories
    return DictResponseModel(data=new_problem,
                             message="Problem added successfully.",
                             code=status.HTTP_200_OK)


@router.post("/{id}/categories",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new problem-category")
async def create_problem_category(id: str, category_id: str):
    problem_category_dict = ProblemCategory(
        problem_id=id,
        category_id=category_id
    ).model_dump()
    new_problem_category = await add_problem_category(problem_category_dict)
    return DictResponseModel(data=new_problem_category,
                             message="Problem-Category added successfully.",
                             code=status.HTTP_200_OK)


# @router.get("/problems",
#             description="Retrieve all problems")
# async def get_problems(user_clerk_id: str = Depends(is_authenticated)):
#     cur_user = await retrieve_user(user_clerk_id)
#     role = cur_user["role"]
#     problems = await retrieve_problems(role)
#     if problems:
#         return ListResponseModel(data=problems,
#                                  message="Problems retrieved successfully.",
#                                  code=status.HTTP_200_OK)
#     return ListResponseModel(data=[],
#                              message="No problems exist.",
#                              code=status.HTTP_404_NOT_FOUND)


@router.get("/problems",
            description="Retrieve all problems")
async def get_problems(
        search: Optional[str] = Query(
            None, description="Search by problem title or description"),
        categories: Optional[List[str]] = Query(
            [], description="Filter by categories"),
        difficulty: Optional[str] = Query(
            None, description="Filter by difficulty"),
        is_published: Optional[bool] = Query(
            None, description="Filter by is_published"),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100)):

    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"difficulty": {"$regex": search, "$options": "i"}},
            {"category_info.category_name": {"$regex": search, "$options": "i"}},

        ]

    if difficulty is not None:
        match_stage["$match"]["difficulty"] = difficulty

    if is_published is not None:
        match_stage["$match"]["is_published"] = is_published

    if len(categories) > 0:
        problem_categories = await retrieve_by_categories(categories)
        if not problem_categories:
            return ListResponseModel(data=[],
                                     message="No problems match with categories.",
                                     code=status.HTTP_404_NOT_FOUND)
        problem_ids = [ObjectId(problem_category["problem_id"])
                       for problem_category in problem_categories]
        match_stage["$match"]["_id"] = {"$in": problem_ids}

    pipeline = [
        {
            "$lookup": {
                "from": "problem_category",
                "localField": "_id",
                "foreignField": "problem_id",
                "as": "problem_categories"
            }
        },
        {
            "$unwind": {
                "path": "$problem_categories",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$lookup": {
                "from": "categories",
                "localField": "problem_categories.category_id",
                "foreignField": "_id",
                "as": "category_info"
            }
        },
        {
            "$unwind": {
                "path": "$category_info",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "problem_data": {"$first": "$$ROOT"},
                "category_info": {"$push": "$category_info"}
            }
        },
        {
            "$replaceRoot": {
                "newRoot": {
                    "$mergeObjects": ["$problem_data", {"category_info": "$category_info"}]
                }
            }
        },
        {
            "$sort": {"_id": 1}
        },
        match_stage,
        {
            "$facet": {
                "problems": [
                    {
                        "$skip": (page - 1) * per_page
                    },
                    {
                        "$limit": per_page
                    }
                ],
                "total": [
                    {
                        "$count": "count"
                    }
                ]
            }
        },
    ]
    problems = await retrieve_search_filter_pagination(pipeline, page, per_page)
    if problems:
        return DictResponseModel(data=problems,
                                 message="Problems retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ListResponseModel(data=[],
                             message="No problems exist.",
                             code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}",
            description="Retrieve a problem with a matching ID")
async def get_problem(id: str):
    problem = await retrieve_problem(id)
    if problem:
        return DictResponseModel(data=problem,
                                 message="Problem retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem was not retrieved.",
                              code=status.HTTP_404_NOT_FOUND)


@router.patch("/{id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a problem with a matching ID")
async def update_problem_data(id: str,
                              problem_data: UpdateProblemSchema = Body(...),
                              user_clerk_id: str = Depends(is_authenticated)):
    problem_dict = problem_data.model_dump()
    category_ids = problem_dict.pop("category_ids", [])
    deleted = await delete_all_by_problem_id(id)
    if not deleted:
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problem-Category was not deleted.",
                                  code=status.HTTP_404_NOT_FOUND)
    new_problem_categories = []
    if len(category_ids) > 0:
        problem_categories: List[dict] = [
            ProblemCategory(problem_id=id,
                            category_id=category_id).model_dump()
            for category_id in category_ids
        ]
        new_problem_categories = await add_more_problem_category(problem_categories)
        if not new_problem_categories:
            return ErrorResponseModel(error="An error occurred.",
                                      message="Problem-Category was not added.",
                                      code=status.HTTP_404_NOT_FOUND)

    updated_data = UpdateProblemSchemaDB(**problem_dict,
                                         creator_id=user_clerk_id)
    updated = await update_problem(id, updated_data.model_dump())
    if updated:
        return ListResponseModel(data=[],
                                 message="Problem data updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem data was not updated.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}/categories/{category_id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Remove a problem-category")
async def delete_problem_category_data(id: str, category_id: str):
    problem_category = await retrieve_by_problem_category_id(id, category_id)
    if problem_category:
        deleted = await delete_problem_category(problem_category["id"])
        if deleted:
            return ListResponseModel(data=[],
                                     message="Problem-Category deleted successfully.",
                                     code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem-Category was not deleted.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a problem with a matching ID")
async def delete_problem_data(id: str):
    deleted = await delete_problem(id)
    if deleted:
        return ListResponseModel(data=[],
                                 message="Problem deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem was not deleted.",
                              code=status.HTTP_404_NOT_FOUND)
