from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/do_exam", log_file="do_exam.log")

try:
    timer_collection = mongo_db["timer"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# helper 
def timer_helper(timer) -> dict:
    return {
        "id": str(timer["_id"]),
        "user_id": timer["user_id"],
        "start_time": timer["start_time"],
    }


async def add_timer(timer_data: dict) -> dict:
    """
    Add a new timer to the database
    Returns:
        dict: timer data
    """
    try:
        timer = await timer_collection.insert_one(timer_data)
        new_timer = await timer_collection.find_one({"_id": timer.inserted_id})
        return timer_helper(new_timer)
    except Exception as e:
        logger.error(f"Error when add timer: {e}")


async def retrieve_timer(user_id: str) -> dict:
    """
    Retrieve a timer from the database
    Args:
        user_id (str): user_id of the timer
    Returns:
        dict: timer data
    """
    try:
        timer = await timer_collection.find_one({"user_id": ObjectId(user_id)})
        if timer:
            return timer_helper(timer)
    except Exception as e:
        logger.error(f"Error when retrieve timer: {e}")
