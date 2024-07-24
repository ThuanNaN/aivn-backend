from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.schemas.timer import (
    TimerSchemaDB
)
from app.api.v1.controllers.timer import (
    retrieve_timer_by_user_id,
    retrieve_timer_by_exam_id,
    add_timer,
    delete_timer_by_exam_user_id
)
from app.schemas.response import (
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_authenticated

router = APIRouter()
logger = Logger("routes/timer", log_file="timer.log")


@router.post("/exam/{exam_id}",
             description="Add a new timer")
async def create_timer(exam_id=str,
                       clerk_user_id: str = Depends(is_authenticated)):
    current_timer = await retrieve_timer_by_user_id(clerk_user_id)
    if current_timer:
        return ErrorResponseModel(error="An error occurred.",
                                  code=status.HTTP_400_BAD_REQUEST,
                                  message="Timer already exists.")
    # create new
    timer_data = TimerSchemaDB(
        exam_id=exam_id,
        clerk_user_id=clerk_user_id
    )
    new_timer = await add_timer(timer_data.model_dump())
    if new_timer:
        return DictResponseModel(data=new_timer,
                                 message="Timer added successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="There was an error adding the timer.")


@router.get("/exam/{exam_id}",
            description="Retrieve a problem with a matching user_id ID")
async def get_problem(exam_id: str):
    timer = await retrieve_timer_by_exam_id(exam_id)
    if timer:
        return DictResponseModel(data=timer,
                                 message="Timer retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="Timer does not exist.")


@router.delete("/exam/{exam_id}",
               description="Delete a timer with a matching user_id")
async def delete_timer(exam_id: str,
                       clerk_user_id: str = Depends(is_authenticated)):
    timer = await delete_timer_by_exam_user_id(exam_id, clerk_user_id)
    if timer:
        return DictResponseModel(data=timer,
                                 message="Timer deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="Timer does not exist.")
