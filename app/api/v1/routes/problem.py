from app.utils.logger import Logger
from fastapi import APIRouter, Body, Depends, status
from app.api.v1.controllers.problem import (
    add_problem,
    retrieve_problems,
    retrieve_problem,
    update_problem,
    delete_problem
)
from app.schemas.problem import (
    ProblemSchema,
    ProblemSchemaDB,
    UpdateProblemSchema,
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.schemas.difficulty import DifficultyEnum
from app.schemas.category import CategoryEnum
from app.core.security import is_admin, is_authenticated
from app.api.v1.controllers.user import retrieve_user

router = APIRouter()
logger = Logger("routes/problem", log_file="problem.log")


@router.get("/difficulties",
            description="Retrieve all difficulties")
def get_difficulties():
    difficulties = DifficultyEnum.get_list()
    return ListResponseModel(data=difficulties,
                             message="Difficulties retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/categories",
            description="Retrieve all categories")
def get_categories():
    categories = CategoryEnum.get_list()
    return ListResponseModel(data=categories,
                             message="Categories retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new problem")
async def create_problem(problem: ProblemSchema, user_clerk_id: str = Depends(is_authenticated)):
    problem_dict = problem.model_dump()
    problem_db = ProblemSchemaDB(**problem_dict, creator_id=user_clerk_id)
    new_problem = await add_problem(problem_db.model_dump())
    return DictResponseModel(data=new_problem,
                             message="Problem added successfully.",
                             code=status.HTTP_200_OK)


@router.get("/problems",
            description="Retrieve all problems")
async def get_problems(user_clerk_id: str = Depends(is_authenticated)):
    cur_user = await retrieve_user(user_clerk_id)
    role = cur_user["role"]
    problems = await retrieve_problems(role)
    if problems:
        return ListResponseModel(data=problems,
                                 message="Problems retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ListResponseModel(data=[],
                             message="No problems exist.",
                             code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}",
            description="Retrieve a problem with a matching ID")
async def get_problem(id: str, user_clerk_id: str = Depends(is_authenticated)):
    cur_user = await retrieve_user(user_clerk_id)
    role = cur_user["role"]
    problem = await retrieve_problem(id, role)
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
async def update_problem_data(id: str, data: UpdateProblemSchema = Body(...)):
    updated = await update_problem(id, data.model_dump())
    if updated:
        return ListResponseModel(data=[],
                                 message="Problem data updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem data was not updated.",
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
