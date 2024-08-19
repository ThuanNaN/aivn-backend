import traceback
from app.utils.time import utc_to_local
from typing import List
from app.core.database import mongo_db
from app.utils.logger import Logger
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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_retakes() -> list:
    """
    Retrieve all retakes from the database
    """
    try:
        retakes = []
        async for retake in retake_collection.find():
            retakes.append(retake_helper(retake))
        return retakes
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
    

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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_retakes_unsubmit(submission_retake_ids: List[str]) -> list:
    """
    Retrieve retakes that have not been submitted
    :return list
    """
    try:
        retakes = await retrieve_retakes()
        retake_ids = [retake["id"] for retake in retakes]
        unsubmit_retake_ids = [retake_id for retake_id in retake_ids if retake_id not in submission_retake_ids]
        unsubmit_retakes = [retake for retake in retakes if retake["id"] in unsubmit_retake_ids]
        return unsubmit_retakes
    except Exception as e:
        logger.error(f"Error when retrieving retakes: {e}")
        return None


async def delete_retake_by_id(id: str) -> bool:
    """
    Delete a retake with a matching ID
    :param id: str
    :return: bool
    """
    try:
        retake = await retake_collection.find_one({"_id": ObjectId(id)})
        if not retake:
            raise Exception("Retake not found")
        
        deleted_retake = await retake_collection.delete_one({"_id": ObjectId(id)})
        if deleted_retake.deleted_count == 1:
            return True
        return False
    except Exception as e:
        logger.error(f"Error when delete retake: {e}")
        return e


async def delete_retakes_by_exam_id(exam_id: str) -> bool:
    """
    Delete retakes with a matching exam ID
    :param exam_id: str
    :return: bool
    """
    try:
        retakes = await retrieve_retake_by_exam_id(exam_id)
        if isinstance(retakes, Exception):
            raise retakes
        if retakes:
            deleted_retakes = await retake_collection.delete_many({"exam_id": ObjectId(exam_id)})
            if deleted_retakes.deleted_count > 0:
                return True
            return False
        else:
            return True # No retake to delete
    except Exception as e:
        logger.error(f"Error when delete retakes: {e}")
        return e

    
async def delete_retake_by_ids(ids: list) -> bool:
    """
    Delete retakes with a matching IDs
    :param ids: list
    :return: bool
    """
    try:
        deleted_retakes = await retake_collection.delete_many({"_id": {"$in": ids}})
        if deleted_retakes.deleted_count > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"Error when delete retakes: {e}")
        return e
