import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from app.core.database import mongo_db


logger = Logger("controllers/shortener", log_file="shortener.log")

try:
    shortener_collection = mongo_db["shortener"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# shortener helper
def shortener_helper(shortener) -> dict:
    return {
        "id": str(shortener["_id"]),
        "original_url": str(shortener["original_url"]),
        "short_url": shortener["short_url"],
        "created_at": utc_to_local(shortener["created_at"]),
        "updated_at": utc_to_local(shortener["updated_at"]),

    }

async def add_short_url(shortener_data: dict) -> dict | MessageException:
    """
    Create a new original-short url into the database
    :param shortener_data: dict
    :return: dict
    """
    try:
        # Check the short url is already exist
        short_url = await shortener_collection.find_one({
            "short_url": shortener_data["short_url"]
        })
        if short_url:
            return MessageException("Short url already exist",
                                    status.HTTP_400_BAD_REQUEST)
        data = await shortener_collection.insert_one(shortener_data)
        new_data = await shortener_collection.find_one({
            "_id": data.inserted_id
        })
        return shortener_helper(new_data)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add new short url",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_short_url(original_url: str) -> dict | MessageException:
    """
    Retrieve a short url by given original url
    :original_url: str
    :return: dict
    """
    try:
        short_url = await shortener_collection.find_one({
            "original_url": original_url
        })
        return shortener_helper(short_url)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve short url",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
        

async def retrieve_original_url(short_url: str) -> dict | MessageException:
    """
    Retrieve a original url by given short url
    :short_url: str
    :return: dict
    """
    try:
        original_url = await shortener_collection.find_one({
            "short_url": short_url
        })
        return shortener_helper(original_url)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve original url",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)