from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.api.v1.controllers.exam_problem import (
    add_exam_problem,
    retrieve_exam_problems,
    retrieve_exam_problem,
    update_exam_problem,
    delete_exam_problem
)
from app.schemas.exam_problem import (
    ExamProblem,
    ExamProblemDB,
    UpdateExamProblem,
    UpdateExamProblemDB
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated

router = APIRouter()
logger = Logger("routes/problem", log_file="problem.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new exam_problem")
async def create_exam_problem(exam_problem: ExamProblem,
                              user_clerk_id: str = Depends(is_authenticated)):
    exam_problem_dict = exam_problem.model_dump()
    exam_problem_db = ExamProblemDB(**exam_problem_dict,
                                    creator_id=user_clerk_id)
    new_exam_problem = await add_exam_problem(exam_problem_db.model_dump())
    return DictResponseModel(data=new_exam_problem,
                             message="ExamProblem added successfully.",
                             code=status.HTTP_200_OK)


@router.get("/exam_problems",
            dependencies=[Depends(is_admin)],
            description="Retrieve all exam_problems")
async def get_exam_problems():
    exam_problems = await retrieve_exam_problems()
    if exam_problems:
        return ListResponseModel(data=exam_problems,
                                 message="ExamProblems retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="Empty list returned.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}",
            dependencies=[Depends(is_admin)],
            description="Retrieve a exam_problem with a matching ID")
async def get_exam_problem(id: str):
    exam_problem = await retrieve_exam_problem(id)
    if exam_problem:
        return DictResponseModel(data=exam_problem,
                                 message="ExamProblem retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="ExamProblem not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            description="Update a exam_problem with a matching ID")
async def update_exam_problem_data(id: str,
                                   exam_problem: UpdateExamProblem,
                                   user_clerk_id=Depends(is_authenticated)):
    exam_problem_dict = exam_problem.model_dump()
    exam_problem_db = UpdateExamProblemDB(**exam_problem_dict,
                                    creator_id=user_clerk_id)
    updated_exam_problem = await update_exam_problem(id, exam_problem_db.model_dump())
    if updated_exam_problem:
        return ListResponseModel(data=[],
                                 message="ExamProblem updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="ExamProblem not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               description="Delete a exam_problem with a matching ID")
async def delete_exam_problem_data(id: str):
    deleted_exam_problem = await delete_exam_problem(id)
    if deleted_exam_problem:
        return ListResponseModel(data=[],
                                 message="ExamProblem deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="ExamProblem not found.",
                              code=status.HTTP_404_NOT_FOUND)
