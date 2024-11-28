from typing import List
from datetime import datetime, UTC
from app.utils import Logger, MessageException
from fastapi import (
    APIRouter, Depends, 
    status, HTTPException
)
from app.schemas.exam import (
    ExamSchema,
    ExamSchemaDB,
    UpdateExamSchema,
    UpdateExamSchemaDB,
    OrderSchema
)
from app.schemas.timer import (
    TimerSchema,
    TimerSchemaDB
)
from app.schemas.exam_problem import (
    UpdateExamProblemDB
)
from app.schemas.retake import (
    RetakeSchema,
    RetakeSchemaDB
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel
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
from app.api.v1.controllers.timer import (
    retrieve_timer_by_exam_retake_user_id,
    add_timer,
    delete_timer_by_exam_user_id
)
from app.api.v1.controllers.retake import (
    add_retake,
    retrieve_retake_by_exam_id,
    delete_retake_by_id
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
async def create_exam(exam: ExamSchema,
                      creator_id: str = Depends(is_authenticated)):
    exam_dict = ExamSchemaDB(
        **exam.model_dump(),
        creator_id=creator_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    ).model_dump()
    new_exam = await add_exam(exam_dict)
    if isinstance(new_exam, MessageException):
        return HTTPException(status_code=new_exam.status_code,
                             detail=new_exam.message)
    return DictResponseModel(data=new_exam,
                             message="Exam added successfully.",
                             code=status.HTTP_200_OK)


@router.post("/{exam_id}/timer",
             dependencies=[Depends(is_authenticated)],
             description="Add a new timer")
async def create_timer(exam_id: str,
                       timer_data: TimerSchema,
                       clerk_user_id: str = Depends(is_authenticated)): 
    timer_dict = timer_data.model_dump()
    timer_data = TimerSchemaDB(
        **timer_dict,
        exam_id=exam_id,
        clerk_user_id=clerk_user_id
    ).model_dump()
    new_timer = await add_timer(timer_data)
    if isinstance(new_timer, MessageException):
        return HTTPException(status_code=new_timer.status_code,
                             detail=new_timer.message)
    
    return DictResponseModel(data=new_timer,
                             message="Timer added successfully.",
                             code=status.HTTP_200_OK)


@router.post("/{exam_id}/retake",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new retake")
async def create_retake(exam_id: str,
                        retake_data: RetakeSchema,
                        clerk_user_id: str = Depends(is_authenticated)):
    retake_db = RetakeSchemaDB(
        **retake_data.model_dump(),
        creator_id=clerk_user_id,
        exam_id=exam_id,
        created_at=datetime.now(UTC)
    ).model_dump()
    new_retake = await add_retake(retake_db)
    if isinstance(new_retake, MessageException):
        return HTTPException(status_code=new_retake.status_code,
                             detail=new_retake.message)
    return DictResponseModel(data=new_retake,
                             message="Retake added successfully.",
                             code=status.HTTP_200_OK)


@router.get("/exams",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all exams")
async def get_exams():
    exams = await retrieve_exams()
    if isinstance(exams, MessageException):
        return HTTPException(status_code=exams.status_code,
                             detail=exams.message)
    return ListResponseModel(data=exams,
                             message="Exams retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a exam with a matching ID")
async def get_exam_by_id(id: str):
    exam = await retrieve_exam(id)
    if isinstance(exam, MessageException):
        return HTTPException(status_code=exam.status_code,
                             detail=exam.message)
    return DictResponseModel(data=exam,
                             message="Exam retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{exam_id}/timer",
            description="Retrieve a timer with a matching exam_id ID")
async def get_timer(exam_id: str, 
                    retake_id: str | None = None,
                    clerk_user_id: str = Depends(is_authenticated)):
    timer = await retrieve_timer_by_exam_retake_user_id(exam_id, 
                                                        clerk_user_id, 
                                                        retake_id)
    if isinstance(timer, MessageException):
        return HTTPException(status_code=timer.status_code,
                             detail=timer.message)
    
    return DictResponseModel(data=timer,
                             message="Timer retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{exam_id}/retake",
            description="Retrieve a all retakes with a matching exam_id ID")
async def get_retake(exam_id: str):
    retake = await retrieve_retake_by_exam_id(exam_id)
    if isinstance(retake, MessageException):
        return HTTPException(status_code=retake.status_code, 
                             detail=retake.message)
    return ListResponseModel(data=retake,
                             message="Retake retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}/detail",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a exam with a matching ID and its problems")
async def get_exam_detail(id: str, clerk_user_id=Depends(is_authenticated)):
    exam_detail = await retrieve_exam_detail(id, clerk_user_id)
    if isinstance(exam_detail, MessageException):
        return HTTPException(status_code=exam_detail.status_code,
                             detail=exam_detail.message)
    return DictResponseModel(data=exam_detail,
                             message="Exam retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a exam with a matching ID")
async def update_exam_data(id: str,
                           exam: UpdateExamSchema,
                           creator_id=Depends(is_authenticated)):
    exam_dict = UpdateExamSchemaDB(
        **exam.model_dump(),
        creator_id=creator_id,
        updated_at=datetime.now(UTC)
    ).model_dump()
    updated_exam = await update_exam(id, exam_dict)
    if isinstance(updated_exam, MessageException):
        return HTTPException(status_code=updated_exam.status_code,
                             detail=updated_exam.message)

    return ListResponseModel(data=[],
                             message="Exam updated successfully.",
                             code=status.HTTP_200_OK)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a exam with a matching ID")
async def delete_exam_data(id: str):
    deleted_exam = await delete_exam(id)
    if isinstance(deleted_exam, MessageException):
        return HTTPException(status_code=deleted_exam.status_code,
                             detail=deleted_exam.message)
    return ListResponseModel(data=[],
                             message="Exam deleted successfully.",
                             code=status.HTTP_200_OK)


@router.delete("/{exam_id}/retake",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a retake with a matching exam_id")
async def delete_retake(retake_id: str):
    deleted_retake = await delete_retake_by_id(retake_id)
    if isinstance(deleted_retake, MessageException):
        return HTTPException(status_code=deleted_retake.status_code,
                             detail=deleted_retake.message)
    return ListResponseModel(data=[],
                             message="Retake deleted successfully.",
                             code=status.HTTP_200_OK)


@router.put("/{id}/order-problem",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Order problems in an exam by index")
async def order_problems_in_exam(id: str, 
                                 orders: List[OrderSchema], 
                                 creator_id=Depends(is_authenticated)):
    for order in orders:
        exam_problem = await retrieve_by_exam_problem_id(exam_id=id,
                                                         problem_id=order.problem_id)
        if isinstance(exam_problem, MessageException):
            return HTTPException(status_code=exam_problem.status_code,
                                 detail=exam_problem.message)
        new_exam_problem = UpdateExamProblemDB(
            index=order.index,
            creator_id=creator_id,
            updated_at=datetime.now(UTC)
        )
        updated_exam_problem = await update_exam_problem(exam_problem["id"],
                                                         new_exam_problem.model_dump())
        if isinstance(updated_exam_problem, MessageException):
            return HTTPException(status_code=updated_exam_problem.status_code,
                                 detail=updated_exam_problem.message)
    return ListResponseModel(data=[],
                             message="Problems ordered successfully.",
                             code=status.HTTP_200_OK)
