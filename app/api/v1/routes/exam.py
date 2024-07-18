from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.schemas.exam import (
    ExamSchema,
    UpdateExamSchema
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
    update_exam,
    delete_exam
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
async def get_exam(id: str):
    exam = await retrieve_exam(id)
    if exam:
        return DictResponseModel(data=exam,
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