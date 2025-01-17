import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from app.core.database import mongo_client, mongo_db
from bson.objectid import ObjectId
from datetime import datetime, UTC


logger = Logger("controllers/submission", log_file="submission.log")

try:
    submission_collection = mongo_db["submissions"]
    draft_submission_collection = mongo_db["draft-submissions"]
    retake_collection = mongo_db["retake"]
    timer_collection = mongo_db["timer"]
    certificate_collection = mongo_db["certificate"]
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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add submission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all submissions",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def retrieve_submission_by_pipeline(pipeline: list) -> list:
    """
    Retrieve all submissions with search filter and pagination
    :param pipeline: list
    """
    try:
        pipeline_results = await submission_collection.aggregate(pipeline).to_list(length=None)
        return pipeline_results
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all submissions",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_submission_by_id(id: str) -> dict:
    """
    Retrieve a submission with a matching ID
    :param id: str
    :return: dict
    """
    try:
        submission = await submission_collection.find_one({"_id": ObjectId(id)})
        if not submission:
            raise MessageException("Submission not found",
                                   status.HTTP_404_NOT_FOUND)
        return submission_helper(submission)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve submission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve submissions",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve submission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def retrieve_submission_by_id_user_retake(exam_id: str,
                                                retake_id: str | None,
                                                clerk_user_id: str,
                                                check_none: bool = True
                                                ) -> bool | dict | MessageException:
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
        if not submission:
            raise MessageException("Submission not found",
                                   status.HTTP_404_NOT_FOUND)
        if check_none and submission["submitted_problems"] is None:
            return False
        return submission_helper(submission)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve submission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_submission(id: str, 
                            submission_data: dict
                            ) -> dict | bool | MessageException:
    """
    Update a submission with a matching ID
    :param id: str
    :param data: dict
    :return: dict
    """
    try:
        if len(submission_data) < 1:
            raise MessageException("No data to update", 
                                   status.HTTP_400_BAD_REQUEST)

        submission_data = update_helper(submission_data)
        updated_submission = await submission_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": submission_data}
        )
        if updated_submission.modified_count == 0:
            raise MessageException("Error when update submission",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update submission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def upsert_draft_submission(draft_submission_data: dict
                                  ) -> dict | bool | MessageException:
    """
    Upsert a draft submission with a matching ID
    :param draft_id: str
    :param submission_data: dict
    :return: dict
    """
    try:        
        draft_submission_data["exam_id"] = ObjectId(draft_submission_data["exam_id"])
        draft_submission_data["clerk_user_id"] = draft_submission_data["clerk_user_id"]
        retake_id = draft_submission_data.get("retake_id", None)
        if retake_id is not None:
            draft_submission_data["retake_id"] = ObjectId(retake_id)

        draft_submission = await draft_submission_collection.update_one(
            {
                "exam_id": draft_submission_data["exam_id"], 
                "clerk_user_id": draft_submission_data["clerk_user_id"], 
                "retake_id": draft_submission_data["retake_id"]
            }, 
            {
                "$set": draft_submission_data,
                "$setOnInsert": {"created_at": datetime.now(UTC)}
            },
            upsert=True
        )
        if draft_submission.upserted_id:
            return {
                "detail": "Draft submission created",
            }
        if draft_submission.modified_count == 0:
            raise MessageException("Error when update draft submission",
                                   status.HTTP_400_BAD_REQUEST)
        return {
            "detail": "Draft submission updated",
        }
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update draft submission",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def delete_submission(id: str) -> bool:
    """
    Delete a submission and retake (if exists) with a matching ID
    :param id: str
    :return: bool
    """
    async with await mongo_client.start_session() as session:
        try:
            async with session.start_transaction():
                submission_info = await retrieve_submission_by_id(id)
                retake_id = ObjectId(submission_info["retake_id"]) if submission_info["retake_id"] else None
                if retake_id:
                    await retake_collection.delete_one({"_id": retake_id}, session=session)

                # Delete timer
                await timer_collection.delete_one(
                    {"exam_id": ObjectId(submission_info["exam_id"]),
                    "retake_id": retake_id,
                    "clerk_user_id": submission_info["clerk_user_id"]}, session=session)

                # Delete certificate
                await certificate_collection.delete_one({"submission_id": ObjectId(submission_info["id"])}, session=session)

                # Delete submission
                await submission_collection.delete_one({"_id": ObjectId(id)}, session=session)

        except:
            logger.error(f"{traceback.format_exc()}")
            return MessageException("Error when delete submission",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return True
