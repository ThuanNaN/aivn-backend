from app.utils.logger import Logger
from fastapi import (
    APIRouter,
    Depends,
    status
)
from app.api.v1.controllers.do_exam import (
    add_timer,
    retrieve_timer_by_user_id
)
from app.schemas.exam import (
    DoExamSchema, 
    DoExamDBSchema,
    ResponseModel, 
    ErrorResponseModel
)
from app.core.security import is_authenticated


router = APIRouter()
logger = Logger("routes/do_exam", log_file="do_exam.log")


@router.post("/timer",
             dependencies=[Depends(is_authenticated)],
             description="Add a new timer")
async def create_timer(timer: DoExamSchema, user_id: str = Depends(is_authenticated)):
    timer_dict = timer.model_dump()

    current_timer = await retrieve_timer_by_user_id(user_id)
    if current_timer:
        return ErrorResponseModel(error="An error occurred.",
                                  code=status.HTTP_400_BAD_REQUEST,
                                  message="Timer already exists.")

    timer_data = DoExamDBSchema(
        **timer_dict,
        user_id=user_id
    )
    new_timer = await add_timer(timer_data.model_dump())
    if new_timer:
        return ResponseModel(data=new_timer,
                             message="Timer added successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="There was an error adding the timer.")


@router.get("/timer",
            description="Retrieve a problem with a matching user_id ID")
async def get_problem(user_id: str = Depends(is_authenticated)):
    timer = await retrieve_timer_by_user_id(user_id)
    if timer:
        return ResponseModel(data=timer,
                             message="Timer retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="Timer does not exist.")
