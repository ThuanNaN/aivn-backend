import traceback
from datetime import datetime, UTC
from app.core.database import mongo_db
from app.utils import (
    MessageException,
    Logger, 
    is_cohort_permission
)
from fastapi import status
from bson.objectid import ObjectId
import inngest
from app.inngest.client import inngest_client


logger = Logger("controllers/timer", log_file="timer.log")

try:
    timer_collection = mongo_db["timer"]
    submission_collection = mongo_db["submissions"]
    user_collection = mongo_db["users"]
    exam_collection = mongo_db["exams"]
    contest_collection = mongo_db["contests"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper
def timer_helper(timer) -> dict:
    retake_id = timer.get("retake_id", None)
    retake_id = str(retake_id) if retake_id else None
    return {
        "id": str(timer["_id"]),
        "exam_id": str(timer["exam_id"]),
        "clerk_user_id": timer["clerk_user_id"],
        "retake_id": retake_id,
        "start_time": timer["start_time"]
    }


def ObjectId_helper(timer: dict) -> dict:
    retake_id = timer.get("retake_id", None)
    if retake_id is not None:
        timer["retake_id"] = ObjectId(retake_id)
    else:
        timer["retake_id"] = None

    timer["exam_id"] = ObjectId(timer["exam_id"])
    return timer


async def add_timer(timer_data_input: dict) -> dict | MessageException:
    """
    Check some things before adding a timer:
    - Check if exam is active
    - Check if the contest is active
    - Check if the cohort of user has the permission
    - Check if the timer already exists
    - Check if the pseudo submission already exists

    Then, add some things:
    - Add a timer
    - Add a pseudo submission

    :param timer_data: dict
        - start_time: str
        - exam_id: str
        - retake_id: str
        - clerk_user_id: str

    :return: dict
    
    """
    try:
        timer_data = ObjectId_helper(timer_data_input)
        exam_id = timer_data["exam_id"]
        retake_id = timer_data["retake_id"]
        clerk_user_id = timer_data["clerk_user_id"]

        # Check if exam is active
        exam_info = await exam_collection.find_one({"_id": exam_id})
        if not exam_info:
            raise MessageException("Exam not found", status.HTTP_404_NOT_FOUND)
        if not exam_info["is_active"]:
            raise MessageException("Exam is not active", status.HTTP_400_BAD_REQUEST)
        

        # Check if the contest is active
        contest_info = await contest_collection.find_one({"_id": exam_info["contest_id"]})
        if not contest_info:
            raise MessageException("Contest not found", status.HTTP_404_NOT_FOUND)
        if not contest_info["is_active"]:
            raise MessageException("Contest is not active", status.HTTP_400_BAD_REQUEST)


        # Check if the cohort of user has the permission
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user_info:
            raise MessageException("User not found", status.HTTP_404_NOT_FOUND)
        user_cohort = user_info["cohort"]
        # limit permission by the main cohort of the user
        if not is_cohort_permission(user_cohort, [user_cohort], contest_info["cohorts"]):
            raise MessageException("You are not allowed to access this exam",
                                   status.HTTP_403_FORBIDDEN)


        # Check if the timer already exists
        timer_info = await timer_collection.find_one({
            "exam_id": exam_id,
            "retake_id": retake_id,
            "clerk_user_id": clerk_user_id
        })
        if timer_info:
            raise MessageException("Timer already exists", status.HTTP_400_BAD_REQUEST)


        # Check if the pseudo submission already exists
        submission_info = await submission_collection.find_one({
                "exam_id": exam_id,
                "retake_id": retake_id,
                "clerk_user_id": clerk_user_id
        })
        if submission_info:
            raise MessageException("Pseudo submission already exists", status.HTTP_400_BAD_REQUEST)
        

        # Add a timer
        inserted_timer = await timer_collection.insert_one(timer_data)
        new_timer = await timer_collection.find_one({"_id": inserted_timer.inserted_id})

        str_exam_id = str(exam_info['_id'])
        str_retake_id = str(timer_data_input["retake_id"]) if timer_data_input["retake_id"] else None
        # Send event to inngest
        await inngest_client.send(
            inngest.Event(
                name="contest/submission",
                id=f"submission-{str_exam_id}-{clerk_user_id}",
                data={
                    "submission_info": {
                        "exam_id": str_exam_id,
                        "clerk_user_id": clerk_user_id,
                        "retake_id": str_retake_id,
                        "submitted_problems": None,
                        "total_score": 0,
                        "max_score": 0,
                        "total_problems": 0,
                        "total_problems_passed": 0,
                        "created_at": datetime.now(UTC).isoformat()
                    },
                    "exam_info": {
                        "id": str_exam_id,
                        "duration": exam_info["duration"],
                    },
                    "contest_info": {
                        "id": str(contest_info["_id"]),
                        "certificate_template": contest_info["certificate_template"]
                    },
                    "user_info": {
                        "fullname": user_info["fullname"] if "fullname" in user_info else user_info["username"],
                        "email": user_info["email"]
                    }
                }
            )
        )

        return timer_helper(new_timer)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_timer_by_user_id(clerk_user_id: str) -> dict:
    """
    Retrieve a timer from the database
    :param clerk_user_id: str
    :return: dict
    """
    try:
        timer = await timer_collection.find_one({"clerk_user_id": clerk_user_id})
        if timer:
            return timer_helper(timer)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_timer_by_exam_id(exam_id: str) -> dict:
    """
    Retrieve a timer from the database
    :param exam_id: str
    :return: dict
    """
    try:
        timer = await timer_collection.find_one({"exam_id": ObjectId(exam_id)})
        if timer:
            return timer_helper(timer)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

async def retrieve_timer_by_exam_retake_user_id(exam_id: str,
                                                clerk_user_id: str,
                                                retake_id: str | None
                                                ) -> dict | MessageException:
    """
    Retrieve a timer with matching exam_id, retake_id and clerk_user_id
    :param exam_id: str
    :param retake_id: str
    :param clerk_user_id: str
    :return: dict
    """
    try:
        if retake_id is not None:
            retake_id = ObjectId(retake_id)

        timer = await timer_collection.find_one({"exam_id": ObjectId(exam_id),
                                                 "retake_id": retake_id,
                                                 "clerk_user_id": clerk_user_id})
        if not timer:
            raise MessageException("Timer not found",
                                   status.HTTP_404_NOT_FOUND)
        return timer_helper(timer)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_timer_by_user_id(clerk_user_id: str) -> bool:
    """
    Delete a timer from the database
    :param clerk_user_id: str
    :return: dict
    """
    try:
        timer = await timer_collection.find_one({"clerk_user_id": clerk_user_id})
        if not timer:
            raise MessageException("Timer not found",
                                   status.HTTP_404_NOT_FOUND)
        deleted_timer = await timer_collection.delete_one(
            {"clerk_user_id": clerk_user_id}
        )
        if deleted_timer.deleted_count == 0:
            raise MessageException("Delete timer field",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_timer_by_exam_id(exam_id: str) -> bool:
    """
    Delete a timer from the database
    :param exam_id: str
    :return: bool
    """
    try:
        timer = await timer_collection.find_one({"exam_id": ObjectId(exam_id)})
        if not timer:
            raise MessageException("Timer not found", 
                                   status.HTTP_404_NOT_FOUND)
        deleted_timer = await timer_collection.delete_one(
            {"exam_id": ObjectId(exam_id)})
        if deleted_timer.deleted_count == 0:
            raise MessageException("Delete timer field",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_timer_by_exam_user_id(exam_id: str, clerk_user_id: str) -> bool | MessageException:
    """
    Delete a timer with matching exam_id and user_id from the database
    :param exam_id: str
    :param clerk_user_id: str
    :return: bool
    """
    try:
        timer = await timer_collection.find_one({"exam_id": ObjectId(exam_id),
                                                 "clerk_user_id": clerk_user_id})
        if not timer:
            raise MessageException("Timer not found", 
                                   status.HTTP_404_NOT_FOUND)
        deleted_timer = await timer_collection.delete_one({
            "exam_id": ObjectId(exam_id),
            "clerk_user_id": clerk_user_id
        })
        if deleted_timer.deleted_count == 0:
            raise MessageException("Delete timer field",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_timer_by_exam_retake_user_id(exam_id: str,
                                              clerk_user_id: str,
                                              retake_id: str | None
                                              ) -> bool:
    """
    Delete a timer with matching exam_id, retake_id and user_id from the database
    :param exam_id: str
    :param retake_id: str
    :param clerk_user_id: str
    :return: bool
    """
    try:
        if retake_id is not None:
            retake_id = ObjectId(retake_id)

        timer = await timer_collection.find_one({"exam_id": ObjectId(exam_id),
                                                 "retake_id": retake_id,
                                                 "clerk_user_id": clerk_user_id})
        if not timer:
            raise MessageException("Timer not found",
                                   status.HTTP_404_NOT_FOUND)
        deleted_timer = await timer_collection.delete_one(
            {"exam_id": ObjectId(exam_id),
             "retake_id": retake_id,
             "clerk_user_id": clerk_user_id})
        if deleted_timer.deleted_count == 0:
            raise MessageException("Delete timer field",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete timer",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
