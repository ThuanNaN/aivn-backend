from app.utils.logger import Logger
from fastapi import (
    APIRouter,
    Depends,
    status
)
from app.api.v1.controllers.do_exam import (
    add_timer,
    retrieve_timer
)
from app.schemas.exam import DoExamSchema, ResponseModel, ErrorResponseModel
from app.core.security import is_authenticated


router = APIRouter()
logger = Logger("routes/do_exam", log_file="do_exam.log")


@router.post("/timer",
             dependencies=[Depends(is_authenticated)],
             tags=["Timer"],
             description="Add a new timer")
async def create_timer(timer: DoExamSchema):
    timer_dict = timer.model_dump()
    new_timer = await add_timer(timer_dict)
    if new_timer:
        return ResponseModel(data=new_timer,
                             message="Timer added successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="There was an error adding the timer.")


@router.get("/timer/{id}",
            description="Retrieve a problem with a matching ID")
async def get_problem(user_id: str = Depends(is_authenticated)):
    problem = await retrieve_timer(user_id)
    if problem:
        return ResponseModel(data=problem,
                             message="Problem retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              code=status.HTTP_404_NOT_FOUND,
                              message="Problem does not exist.")
