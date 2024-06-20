from app.utils.logger import Logger
from fastapi import APIRouter, Body
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
    ResponseModel,
    ErrorResponseModel
)

router = APIRouter()
logger = Logger("routes/problem", log_file="problem.log")


@router.post("/problem", description="Add a new problem")
async def create_problem(problem: ProblemSchema):
    try:
        problem_dict = problem.model_dump()
        new_problem = await add_problem(problem_dict)

    except Exception as e:
        logger.error(f"Error when add problem: {e}")
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problem was not added.",
                                  code=400)
    
    return ResponseModel(data=[new_problem],
                         message="Problem added successfully.",
                         code=200)


@router.get("/problems", description="Retrieve all problems")
async def get_problems():
    try:
        problems = await retrieve_problems()
    except Exception as e:
        print(f"Error when retrieve problems: {e}")
        logger.error(f"Error when retrieve problems: {e}")
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problems were not retrieved.",
                                  code=400)
    if problems:
        return ResponseModel(data=problems,
                             message="Problems retrieved successfully.",
                             code=200)
    return ResponseModel(data=[],
                         message="No problems exist.",
                         code=200)


@router.get("/problem/{id}", description="Retrieve a problem with a matching ID")
async def get_problem(id):
    try:
        problem = await retrieve_problem(id)
        if problem:
            return ResponseModel(data=[problem],
                                message="Problem retrieved successfully.",
                                code=200)
    except Exception as e:
        logger.error(f"Error when retrieve problem: {e}")
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problem was not retrieved.",
                                  code=404)


@router.patch("/problem/{id}", description="Update a problem with a matching ID")
async def update_problem_data(id: str, data: UpdateProblemSchema = Body(...)):
    try:
        updated = await update_problem(id, data.model_dump())
        if updated:
            return ResponseModel(data=[],
                                message="Problem data updated successfully.",
                                code=200)
    except Exception as e:
        logger.error(f"Error when update problem: {e}")
        return ErrorResponseModel(error="An error occurred.",
                                message="Problem data was not updated.",
                                code=404)


@router.delete("/problem/{id}", description="Delete a problem with a matching ID")
async def delete_problem_data(id: str):
    try:
        deleted = await delete_problem(id)
        if deleted:
            return ResponseModel(data=[],
                                message="Problem deleted successfully.",
                                code=200)
    except Exception as e:
        logger.error(f"Error when delete problem: {e}")
        return ErrorResponseModel(error="An error occurred.",
                                message="Problem was not deleted.",
                                code=404)
