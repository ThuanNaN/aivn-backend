import traceback
from app.utils.time import utc_to_local
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.retake import (
    retrieve_retakes_by_user_exam_id,
    delete_retake_by_ids
)
from app.api.v1.controllers.timer import (
    delete_timer_by_exam_retake_user_id
)
from app.api.v1.controllers.certificate import (
    delete_certificate_by_submission_id
)

logger = Logger("controllers/submission", log_file="submission.log")

try:
    submission_collection = mongo_db["submissions"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# submission helper
def submission_helper(submission) -> dict:
    retake_id = submission.get("retake_id", None)
    retake_id = str(retake_id) if retake_id else None
    return {
        "id": str(submission["_id"]),
        "exam_id": str(submission["exam_id"]),
        "clerk_user_id": submission["clerk_user_id"],
        "retake_id": retake_id,
        "submitted_problems": submission["submitted_problems"],
        "total_problems": submission["total_problems"],
        "total_score": submission["total_score"],
        "max_score": submission["max_score"],
        "created_at": utc_to_local(submission["created_at"]),
    }


def ObjectId_helper(submission: dict) -> dict:
    retake_id = submission.get("retake_id", None)
    if retake_id is not None:
        submission["retake_id"] = ObjectId(retake_id)
    else:
        submission["retake_id"] = None

    submission["exam_id"] = ObjectId(submission["exam_id"])
    return submission


def update_helper(submission: dict) -> dict:
    retake_id = submission.get("retake_id", None)
    if retake_id is not None:
        submission["retake_id"] = ObjectId(retake_id)
    else:
        submission["retake_id"] = None
    return submission


async def add_submission(submission_data: dict) -> dict:
    """
    Create a new submission in the database
    :param submission_data: dict
    :return: dict
    """
    try:
        submission_data = ObjectId_helper(submission_data)
        submission = await submission_collection.insert_one(submission_data)
        new_submission = await submission_collection.find_one(
            {"_id": submission.inserted_id}
        )
        return submission_helper(new_submission)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_submissions() -> list:
    """
    Retrieve all submissions from database
    :return: list
    """
    try:
        submissions = []
        async for submission in submission_collection.find():
            return_data = submission_helper(submission)
            submissions.append(return_data)
        return submissions
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



async def retrieve_submission_by_pipeline(pipeline: list) -> list:
    """
    Retrieve all submissions with search filter and pagination
    :param pipeline: list
    """
    try:
        pipeline_results = await submission_collection.aggregate(pipeline).to_list(length=None)
        return pipeline_results
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_submission_by_id(id: str) -> dict:
    """
    Retrieve a submission with a matching ID
    :param id: str
    :return: dict
    """
    try:
        submission = await submission_collection.find_one({"_id": ObjectId(id)})
        if not submission:
            raise Exception("Submission not found")
        return submission_helper(submission)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_submission_by_exam_id(exam_id: str) -> list:
    """
    Retrieve all submissions by exam ID
    :param exam_id: str
    :return: list
    """
    try:
        submissions = []
        async for submission in submission_collection.find({"exam_id": ObjectId(exam_id)}):
            return_data = submission_helper(submission)
            submissions.append(return_data)
        return submissions
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_submission_by_exam_user_id(exam_id: str,
                                              clerk_user_id
                                              ) -> dict:
    """
    Retrieve a submission by exam ID and user ID
    :param exam_id: str
    :param clerk_user_id: str
    :return dict
    """
    try:
        submission = await submission_collection.find_one(
            {"exam_id": ObjectId(exam_id), "clerk_user_id": clerk_user_id}
        )
        if submission:
            return_data = submission_helper(submission)
            return return_data
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



async def retrieve_submission_by_id_user_retake(exam_id: str,
                                                retake_id: str | None,
                                                clerk_user_id: str,
                                                check_none: bool = True
                                                ) -> dict:
    """
    Retrieve a submission by exam ID, retake ID and user ID
    :param exam_id: str
    :param retake_id: str
    :param clerk_user_id: str
    :return dict
    """
    try:
        if retake_id is not None:
            retake_id = ObjectId(retake_id)

        submission = await submission_collection.find_one(
            {
                "exam_id": ObjectId(exam_id),
                "retake_id": retake_id,
                "clerk_user_id": clerk_user_id
            }
        )
        if submission:
            if check_none and submission["submitted_problems"] is None:
                return None
            return submission_helper(submission)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def update_submission(id: str, submission_data: dict) -> dict:
    """
    Update a submission with a matching ID
    :param id: str
    :param data: dict
    :return: dict
    """
    try:
        if len(submission_data) < 1:
            raise Exception("No data to update")

        submission_data = update_helper(submission_data)
        updated_submission = await submission_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": submission_data}
        )
        if updated_submission.modified_count > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


# TODO: Add transaction
async def delete_submission(id: str) -> bool:
    """
    Delete a submission and retake (if exists) with a matching ID
    :param id: str
    :return: bool
    """
    try:
        submission = await submission_collection.find_one({"_id": ObjectId(id)})
        if not submission:
            raise Exception("Submission not found")
        
        submission_info = await retrieve_submission_by_id(id)
        if isinstance(submission_info, Exception):
            raise submission_info

        clerk_user_id = submission_info["clerk_user_id"]

        # Delete retake if exists
        retakes = await retrieve_retakes_by_user_exam_id(clerk_user_id=clerk_user_id, 
                                                        exam_id=submission_info["exam_id"])        
        if isinstance(retakes, Exception):
            raise retakes
        if retakes:
            retake_ids = [ObjectId(retake["id"]) for retake in retakes]
            deleted_retakes = await delete_retake_by_ids(retake_ids)
            if isinstance(deleted_retakes, Exception):
                raise deleted_retakes
            if not deleted_retakes:
                raise Exception("Delete retake failed.")


        # Delete timer
        deleted_timer = await delete_timer_by_exam_retake_user_id(exam_id=submission_info["exam_id"],
                                                                clerk_user_id=clerk_user_id,
                                                                retake_id=submission_info["retake_id"])
        if isinstance(deleted_timer, Exception):
            raise deleted_timer
        if not deleted_timer:
            raise Exception("Delete timer failed.")


        # Delete certificate if exists
        deleted_certificate = await delete_certificate_by_submission_id(id)
        if isinstance(deleted_certificate, Exception):
            raise deleted_certificate


        # Delete submission
        submission = await submission_collection.find_one({"_id": ObjectId(id)})
        if not submission:
            raise Exception("Submission not found")
        deleted_submission = await submission_collection.delete_one({"_id": ObjectId(id)})
        if deleted_submission.deleted_count == 1:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e

