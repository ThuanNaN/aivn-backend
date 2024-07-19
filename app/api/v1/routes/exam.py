from typing import List
from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.schemas.exam import (
    ExamSchema,
    UpdateExamSchema,
    OrderSchema
)
from app.schemas.exam_problem import (
    UpdateExamProblem
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated
from app.api.v1.controllers.exam import (
    add_exam,
    retrieve_exams,
    retrieve_exam,
    retrieve_exam_detail,
    update_exam,
    delete_exam
)
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_problem_id,
    update_exam_problem
)

router = APIRouter()
logger = Logger("routes/exam", log_file="exam.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new exam")
async def create_exam(exam: ExamSchema):
    exam_dict = exam.model_dump()
    new_exam = await add_exam(exam_dict)
    if new_exam:
        return DictResponseModel(data=new_exam,
                                 message="Exam added successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="An error occurred",
                              code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/exams",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all exams")
async def get_exams():
    exams = await retrieve_exams()
    if exams:
        return ListResponseModel(data=exams,
                                 message="Exams retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="An error occurred",
                              code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a exam with a matching ID")
async def get_exam_by_id(id: str):
    exam = await retrieve_exam(id)
    if exam:
        return DictResponseModel(data=exam,
                                 message="Exam retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="An error occurred",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}/detail",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a exam with a matching ID and its problems")
async def get_exam_detail(id: str):
    exam_detail = await retrieve_exam_detail(id)
    if exam_detail:
        return DictResponseModel(data=exam_detail,
                                 message="Exam retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="An error occurred",
                              code=status.HTTP_404_NOT_FOUND)


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a exam with a matching ID")
async def update_exam_data(id: str, exam: UpdateExamSchema):
    exam_dict = exam.model_dump()
    updated_exam = await update_exam(id, exam_dict)
    if updated_exam:
        return ListResponseModel(data=[],
                                 message="Exam updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="An error occurred",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a exam with a matching ID")
async def delete_exam_data(id: str):
    deleted_exam = await delete_exam(id)
    if deleted_exam:
        return ListResponseModel(data=[],
                                 message="Exam deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred",
                              message="An error occurred",
                              code=status.HTTP_404_NOT_FOUND)


@router.put("/{id}/order-problem",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Order problems in an exam by index")
async def order_problems_in_exam(id: str, orders: List[OrderSchema]):
    for order in orders:
        # order -> {
        #     "exam_id": "6698921e0ab511463f14d0a9",
        #     "problem_id": "6698921e0ab511463f14d0a9",
        #     "index": 1
        # }
        exam_problem = await retrieve_by_exam_problem_id(exam_id=id,
                                                         problem_id=order["problem_id"])
        new_exam_problem = UpdateExamProblem(
            index=order["index"]
        )
        updated = await update_exam_problem(exam_problem["id"],
                                            new_exam_problem.model_dump())
        if not updated:
            return ErrorResponseModel(error="An error occurred",
                                      message="An error occurred",
                                      code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=[],
                             message="Problems ordered successfully.",
                             code=status.HTTP_200_OK)
