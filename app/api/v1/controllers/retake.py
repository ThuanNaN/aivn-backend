import traceback
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
        "user_clerk_id": retake["user_clerk_id"],
        "creator_id": retake["creator_id"],
        "exam_id": str(retake["exam_id"]),
        "created_at": str(retake["created_at"]),
        "updated_at": str(retake["updated_at"])
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


async def retrieve_retake_by_user_clerk_id(user_clerk_id: str) -> list:
    """
    Retrieve retakes with a matching user_clerk_id
    :param user_clerk_id: str
    :return: list
    """
    try:
        retakes = []
        async for retake in retake_collection.find({"user_clerk_id": user_clerk_id}):
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
    

async def update_retake(id: str, retake_data: dict) -> bool:
    """
    Update a retake with a matching ID
    :param id: str
    :param retake_data: dict
    :return: bool
    """
    try:
        if len(retake_data) < 1:
            raise Exception("No data to update")
        
        retake = await retake_collection.find_one({"_id": ObjectId(id)})
        if not retake:
            raise Exception("Retake not found")
        
        updated_retake = await retake_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": retake_data}
        )
        if updated_retake.modified_count == 1:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


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