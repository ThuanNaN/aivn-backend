from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.api.v1.controllers.submission import (
    retrieve_submissions
)
from app.api.v1.controllers.retake import (
    retrieve_retakes,
    retrieve_retakes_unsubmit
)
from app.api.v1.controllers.user import retrieve_user
from app.api.v1.controllers.exam import retrieve_exam
from app.api.v1.controllers.contest import retrieve_contest
from app.schemas.response import (
    ListResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated

router = APIRouter()
logger = Logger("routes/retake", log_file="retake.log")


@router.get("/{unsubmit}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all retakes that have not been submitted")
async def get_retakes_unsubmit(unsubmit: bool = True):
    try:
        if not unsubmit:
            retakes_data = await retrieve_retakes()
        else:
            submissions = await retrieve_submissions()
            submission_retake_ids = [submission["retake_id"] for submission in submissions 
                                     if submission["retake_id"]]
            retakes_data = await retrieve_retakes_unsubmit(submission_retake_ids)

        for retake in retakes_data:
            user_info = await retrieve_user(retake["clerk_user_id"])
            if isinstance(user_info, Exception):
                raise user_info

            exam_info = await retrieve_exam(retake["exam_id"])
            if isinstance(exam_info, Exception):
                raise exam_info

            contest_info = await retrieve_contest(exam_info["contest_id"])
            if isinstance(contest_info, Exception):
                raise contest_info

            retake["user"] = user_info
            retake["exam"] = exam_info
            retake["contest"] = contest_info
        return ListResponseModel(data=retakes_data,
                                 message="Retakes unsubmit retrieved successfully",
                                 code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"{e}")
        return ErrorResponseModel(error=str(e),
                                  message="An error occurred while retrieving retakes unsubmit",
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
