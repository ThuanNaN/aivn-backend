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
    problem_dict = problem.model_dump()
    new_problem = await add_problem(problem_dict)
    return ResponseModel(data=new_problem,
                         message="Problem added successfully.",
                         code=200)


@router.get("/problems", description="Retrieve all problems")
async def get_problems():
    problems = await retrieve_problems()
    if problems:
        return ResponseModel(data=problems,
                             message="Problems retrieved successfully.",
                             code=200)
    return ResponseModel(data=[],
                         message="No problems exist.",
                         code=404)


@router.get("/problem/{id}", description="Retrieve a problem with a matching ID")
async def get_problem(id: str):
    problem = await retrieve_problem(id)
    if problem:
        return ResponseModel(data=problem,
                            message="Problem retrieved successfully.",
                            code=200)
    return ErrorResponseModel(error="An error occurred.",
                                message="Problem was not retrieved.",
                                code=404)


@router.patch("/problem/{id}", description="Update a problem with a matching ID")
async def update_problem_data(id: str, data: UpdateProblemSchema = Body(...)):
    updated = await update_problem(id, data.model_dump())
    if updated:
        return ResponseModel(data=[],
                            message="Problem data updated successfully.",
                            code=200)
    return ErrorResponseModel(error="An error occurred.",
                            message="Problem data was not updated.",
                            code=404)


@router.delete("/problem/{id}", description="Delete a problem with a matching ID")
async def delete_problem_data(id: str):
    deleted = await delete_problem(id)
    if deleted:
        return ResponseModel(data=[],
                            message="Problem deleted successfully.",
                            code=200)
    return ErrorResponseModel(error="An error occurred.",
                            message="Problem was not deleted.",
                            code=404)

@router.get("/order", description="Order all problems by date created")
async def order_problems():
    problems = await retrieve_problems()
    sorted_problems = sorted(problems, key=lambda x: x['created_at'])
    sorted_info = []
    for i, problem_data in enumerate(sorted_problems):
        problem_data["index"] = i
        await update_problem(id, problem_data)
        sorted_info.append({
            "id": problem_data["id"],
            "index": i
        })
    return ResponseModel(data=sorted_info,
                         message="Problems ordered successfully.",
                         code=200)