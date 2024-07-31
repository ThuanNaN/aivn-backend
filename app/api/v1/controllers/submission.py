import traceback
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.user import (
    retrieve_user, 
    user_helper
)
from app.api.v1.controllers.exam import (
    retrieve_exam, 
    exam_helper
)
from app.api.v1.controllers.contest import (
    retrieve_contest, 
    contest_helper
)

logger = Logger("controllers/submission", log_file="submission.log")

try:
    submission_collection = mongo_db["submissions"]
except Exception as e:
    logger.error(f"Error when connect to submissions: {e}")
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
        "created_at": str(submission["created_at"]),
    }


async def add_submission(submission_data: dict) -> dict:
    """
    Create a new submission in the database
    :param submission_data: dict
    :return: dict
    """
    try:
        submission_data["exam_id"] = ObjectId(submission_data["exam_id"])
        submission_data["retake_id"] = ObjectId(submission_data["retake_id"])
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
            user_info = await retrieve_user(submission["clerk_user_id"])
            if isinstance(user_info, Exception):
                raise user_info
            return_data = submission_helper(submission)
            return_data["user"] = user_info
            submissions.append(return_data)
        return submissions
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_search_filter_pagination(pipeline: list,
                                            page: int,
                                            per_page: int
                                            ) -> dict:
    """
    Retrieve all submissions with search filter and pagination
    :param pipeline: list
    """
    try:
        pipeline_results = await submission_collection.aggregate(pipeline).to_list(length=None)
        submissions = pipeline_results[0]["submissions"]
        if len(submissions) < 1:
            return {
                "submissions_data": [],
                "total_submissions": 0,
                "total_pages": 0,
                "current_page": page,
                "per_page": per_page
            }
        
        total_submissions = pipeline_results[0]["total"][0]["count"]
        total_pages = (total_submissions + per_page - 1) // per_page

        submissions_data = []
        for submission in submissions:
            submissions_data.append(
                {
                    **submission_helper(submission),
                    "contest_info": contest_helper(submission["contest_info"]),
                    "exam_info": exam_helper(submission["exam_info"]),
                    "user_info": user_helper(submission["user_info"])
                }
            )
        return {
            "submissions_data": submissions_data,
            "total_submissions": total_submissions,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }
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
        
        user_info = await retrieve_user(submission["clerk_user_id"])
        if isinstance(user_info, Exception):
            raise user_info
        
        exam_info = await retrieve_exam(submission["exam_id"])
        if isinstance(exam_info, Exception):
            raise exam_info
        
        contest_info = await retrieve_contest(exam_info["contest_id"])
        if isinstance(contest_info, Exception):
            raise contest_info

        return_data = submission_helper(submission)
        return_data["user"] = user_info
        return_data["exam"] = {
            **exam_info,
            "contest": contest_info
        }
        return return_data
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_submission_by_exam_user_id(exam_id: str, clerk_user_id) -> dict:
    try:
        submission = await submission_collection.find_one(
            {"exam_id": ObjectId(exam_id), "clerk_user_id": clerk_user_id}
        )
        if submission:
            return_data = submission_helper(submission)
            user_info = await retrieve_user(submission["clerk_user_id"])
            if isinstance(user_info, Exception):
                raise user_info
            return_data["user"] = user_info
            return return_data
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_submission(id: str) -> bool:
    """
    Delete a submission with a matching ID
    :param id: str
    :return: bool
    """
    try:
        submission = await submission_collection.find_one({"_id": ObjectId(id)})
        if not submission:
            raise Exception("Submission not found")
        deleted_submission = await submission_collection.delete_one(
            {"_id": ObjectId(id)})
        if deleted_submission.deleted_count == 1:
            return True 
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
