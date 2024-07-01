from typing import List
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
    UpdateProblemSchema,
    OrderSchema,
    ResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin

router = APIRouter()
logger = Logger("routes/problem", log_file="problem.log")


@router.post("/problem",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new problem")
async def create_problem(problem: ProblemSchema):
    problem_dict = problem.model_dump()
    new_problem = await add_problem(problem_dict)
    return ResponseModel(data=new_problem,
                         message="Problem added successfully.",
                         code=status.HTTP_200_OK)


@router.get("/problems",
            description="Retrieve all problems")
async def get_problems():
    problems = await retrieve_problems()
    if problems:
        return ResponseModel(data=problems,
                             message="Problems retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ResponseModel(data=[],
                         message="No problems exist.",
                         code=status.HTTP_404_NOT_FOUND)


@router.get("/problem/{id}",
            description="Retrieve a problem with a matching ID")
async def get_problem(id: str):
    problem = await retrieve_problem(id)
    if problem:
        return ResponseModel(data=problem,
                             message="Problem retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem was not retrieved.",
                              code=status.HTTP_404_NOT_FOUND)


@router.patch("/problem/{id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a problem with a matching ID")
async def update_problem_data(id: str, data: UpdateProblemSchema = Body(...)):
    updated = await update_problem(id, data.model_dump())
    if updated:
        return ResponseModel(data=[],
                             message="Problem data updated successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem data was not updated.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/problem/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a problem with a matching ID")
async def delete_problem_data(id: str):
    deleted = await delete_problem(id)
    if deleted:
        return ResponseModel(data=[],
                             message="Problem deleted successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Problem was not deleted.",
                              code=status.HTTP_404_NOT_FOUND)


@router.put("/order-problem",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Order all problems by date created")
async def order_problems(orders: List[OrderSchema]):
    for order in orders:
        problem_data = await retrieve_problem(order.problem_id)
        problem_data["index"] = order.index
        updated = await update_problem(order.problem_id, problem_data)
        if not updated:
            return ErrorResponseModel(error="An error occurred.",
                                      message="Problem data was not updated.",
                                      code=status.HTTP_404_NOT_FOUND)
    return ResponseModel(data=[],
                         message="Problems ordered successfully.",
                         code=status.HTTP_200_OK)
