import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from bson.objectid import ObjectId
from app.core.database import mongo_db

logger = Logger("controllers/category", log_file="category.log")

try:
    category_collection = mongo_db["categories"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# category helper
def category_helper(category) -> dict:
    return {
        "id": str(category["_id"]),
        "category_name": category["category_name"],
        "created_at": utc_to_local(category["created_at"]),
        "updated_at": utc_to_local(category["updated_at"])
    }

async def add_category(category_data: dict) -> dict:
    """
    Create a new category in the database
    :param category_data: dict
    :return: dict
    """
    try:
        category = await category_collection.insert_one(category_data)
        new_category = await category_collection.find_one(
            {"_id": category.inserted_id}
        )
        return category_helper(new_category)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_categories() -> list:
    """
    Retrieve all categories from database
    :return: list
    """
    try:
        categories = []
        async for category in category_collection.find():
            categories.append(category_helper(category))
        return categories
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve categories",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_category(id: str) -> dict:
    """
    Retrieve a category with a matching ID
    :param id: str
    :return: dict
    """
    try:
        category = await category_collection.find_one({"_id": ObjectId(id)})
        if category:
            return category_helper(category)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

async def update_category(id: str, data: dict) -> bool:
    """
    Update a category with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise MessageException("No data provided to update.", 
                                   status.HTTP_400_BAD_REQUEST)
        update_result = await category_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if update_result.modified_count == 0:
            raise MessageException("Update category failed",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)