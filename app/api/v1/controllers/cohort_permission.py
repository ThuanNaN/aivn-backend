import traceback
from fastapi import status
from app.core.database import mongo_db
from bson.objectid import ObjectId
from app.utils.logger import Logger
from app.utils import (
    MessageException,
    is_cohort_permission
)

logger = Logger("controllers/cohort_permission", log_file="cohort_permission.log")
try:
    user_collection = mongo_db["users"]
    meeting_collection = mongo_db["meetings"]
    contest_collection = mongo_db["contests"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


async def is_contest_permission(id: str | ObjectId, 
                                clerk_user_id: str,
                                return_item: bool = False
                                ) -> bool | tuple | MessageException:
    """
    Check if the user has permission to access the contest
    :param id: str | ObjectId
    :param clerk_user_id: str
    :return: bool
    """
    try:
        permission = False
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user_info:
            raise MessageException("User not found",
                                   status.HTTP_404_NOT_FOUND)
        user_cohort = user_info["cohort"]

        if not isinstance(id, ObjectId):
            id = ObjectId(id)
        contest = await contest_collection.find_one({"_id": id})
        if not contest:
            raise MessageException("Contest not found",
                                   status.HTTP_404_NOT_FOUND)
        # limit permission by the main cohort of the user
        if is_cohort_permission(user_cohort, [user_cohort], contest["cohorts"]):
            permission = True
        if return_item:
            return contest, permission
        return permission
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when check cohort permission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def is_meeting_permission(query_params: dict,
                                clerk_user_id: str,
                                return_item: bool = False
                                ) -> bool | tuple | MessageException:
    """
    Check if the user has permission to access the meeting
    :param id: str | ObjectId
    :param clerk_user_id: str
    :return: bool
    """
    try:
        permission = False
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user_info:
            raise MessageException("User not found",
                                   status.HTTP_404_NOT_FOUND)
        user_cohort = user_info["cohort"]
        feasible_cohort = user_info["feasible_cohort"]

        meeting = await meeting_collection.find_one(query_params)
        if not meeting:
            raise MessageException("Meeting not found",
                                   status.HTTP_404_NOT_FOUND)
        if is_cohort_permission(user_cohort, feasible_cohort, meeting["cohorts"]):
            permission = True
        if return_item:
            return meeting, permission
        return permission
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when check cohort permission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
