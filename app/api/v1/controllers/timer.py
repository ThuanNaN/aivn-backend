from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/timer", log_file="timer.log")

try:
    timer_collection = mongo_db["timer"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# helper 
def timer_helper(timer) -> dict:
    return {
        "id": str(timer["_id"]),
        "clerk_user_id": timer["clerk_user_id"],
        "start_time": timer["start_time"]
    }


async def add_timer(timer_data: dict) -> dict:
    """
    Add a new timer to the database
    :param timer_data: dict
    :return: dict
    """
    try:
        timer = await timer_collection.insert_one(timer_data)
        new_timer = await timer_collection.find_one({"_id": timer.inserted_id})
        return timer_helper(new_timer)
    except Exception as e:
        logger.error(f"Error when add timer: {e}")


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
    except Exception as e:
        logger.error(f"Error when retrieve timer: {e}")


async def delete_timer_by_user_id(clerk_user_id: str) -> dict:
    """
    Delete a timer from the database
    :param clerk_user_id: str
    :return: dict
    """
    try:
        timer = await timer_collection.find_one({"clerk_user_id": clerk_user_id})
        if timer:
            await timer_collection.delete_one({"clerk_user_id": clerk_user_id})
            return True
    except Exception as e:
        logger.error(f"Error when delete timer: {e}")