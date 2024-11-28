import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from typing import List
from app.core.database import mongo_db
from bson.objectid import ObjectId

logger = Logger("controllers/retake", log_file="retake.log")

try:
    retake_collection = mongo_db["retake"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper 
def retake_helper(retake) -> dict:
    return {
        "id": str(retake["_id"]),
        "clerk_user_id": retake["clerk_user_id"],
        "creator_id": retake["creator_id"],
        "exam_id": str(retake["exam_id"]),
        "created_at": utc_to_local(retake["created_at"]),
    }


async def add_retake(retake_data: dict) -> dict:
    """
    Add a new retake into database
    :param retake_data: a dict
    :return: dict
    """
    try:
        retake_data["exam_id"] = ObjectId(retake_data["exam_id"])
        retake = await retake_collection.insert_one(retake_data)
        new_retake = await retake_collection.find_one({"_id": retake.inserted_id})
        return retake_helper(new_retake)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add retake",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_retakes() -> list:
    """
    Retrieve all retakes from the database
    """
    try:
        retakes = []
        async for retake in retake_collection.find():
            retakes.append(retake_helper(retake))
        return retakes
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_retake_by_id(id: str) -> list:
    """
    Retrieve retakes with a matching IDs
    :param ids: list
    :return: list
    """
    try:
        retakes = []
        async for retake in retake_collection.find({"_id": ObjectId(id)}):
            retakes.append(retake_helper(retake))
        return retakes
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retake",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
                                
    

async def retrieve_retakes_by_ids(ids: list) -> list:
    """
    Retrieve retakes with a matching IDs
    :param ids: list
    :return: list
    """
    try:
        retakes = []
        async for retake in retake_collection.find({"_id": {"$in": ids}}):
            retakes.append(retake_helper(retake))
        return retakes
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_retake_by_clerk_user_id(clerk_user_id: str) -> list:
    """
    Retrieve retakes with a matching clerk_user_id
    :param clerk_user_id: str
    :return: list
    """
    try:
        retakes = []
        async for retake in retake_collection.find({"clerk_user_id": clerk_user_id}):
            retakes.append(retake_helper(retake))
        return retakes
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_retake_by_exam_id(exam_id: str) -> list:
    """
    Retrieve retakes with a matching exam_id
    :param exam_id: str
    :return: list
    """
    try:
        retakes = []
        async for retake in retake_collection.find({"exam_id": ObjectId(exam_id)}):
            retakes.append(retake_helper(retake))
        return retakes
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_retakes_by_user_exam_id(clerk_user_id: str, 
                                          exam_id: str
                                          ) -> list:
    """
    Retrieve retakes with a matching clerk_user_id and exam_id
    :param clerk_user_id: str
    :param exam_id: str
    :return: list
    """
    try:
        retakes = []
        async for retake in retake_collection.find(
            {
                "clerk_user_id": clerk_user_id,
                "exam_id": ObjectId(exam_id)
            }
        ):
            retakes.append(retake_helper(retake))
        return retakes
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_retakes_unsubmit(submission_retake_ids: List[ObjectId]) -> list | MessageException:
    """
    Retrieve retakes that have not been submitted
    :return list
    """
    try:
        retake_pipeline = [
            {"$match": {"_id": {"$nin": submission_retake_ids}}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "clerk_user_id",
                    "foreignField": "clerk_user_id",
                    "as": "user_info"
                }
            },
            {
                "$unwind": "$user_info"
            },
            {
                "$lookup": {
                    "from": "exams",
                    "localField": "exam_id",
                    "foreignField": "_id",
                    "as": "exam_info"
                }
            },
            {
                "$unwind": "$exam_info"
            },
            {
                "$lookup": {
                    "from": "contests",
                    "localField": "exam_info.contest_id",
                    "foreignField": "_id",
                    "as": "contest_info"
                }
            },
            {
                "$unwind": "$contest_info"
            },
        ]
        retakes = await retake_collection.aggregate(retake_pipeline).to_list(length=None)
        return retakes
    except:
        logger.error(f"Error when retrieving retakes: {e}")
        return MessageException("Error when retrieve retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_retake_by_id(id: str) -> bool | MessageException:
    """
    Delete a retake with a matching ID
    :param id: str
    :return: bool
    """
    try:
        retake = await retake_collection.find_one({"_id": ObjectId(id)})
        if not retake:
            raise MessageException("Retake not found", 
                                   status.HTTP_404_NOT_FOUND)
        
        deleted_retake = await retake_collection.delete_one({"_id": ObjectId(id)})
        if deleted_retake.deleted_count == 0:
            raise MessageException("Error when delete retake",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"Error when delete retake: {e}")
        return MessageException("Error when delete retake",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)

    
async def delete_retake_by_ids(ids: list) -> bool:
    """
    Delete retakes with a matching IDs
    :param ids: list
    :return: bool
    """
    try:
        deleted_retakes = await retake_collection.delete_many({"_id": {"$in": ids}})
        if deleted_retakes.deleted_count == 0:
            raise MessageException("Error when delete retakes",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"Error when delete retakes: {e}")
        return MessageException("Error when delete retakes",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
