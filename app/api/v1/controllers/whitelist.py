import traceback
from fastapi import status
from app.utils import utc_to_local, MessageException,Logger
from app.core.database import mongo_client, mongo_db
from bson.objectid import ObjectId
from pymongo import UpdateOne, DeleteOne

logger = Logger("controllers/user", log_file="user.log")

try:
    whitelist_collection = mongo_db["whitelists"]
    user_collection = mongo_db["users"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# Helper
def whitelist_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "cohort": user["cohort"],
        "nickname": user["nickname"],
        "created_at": utc_to_local(user["created_at"]),
        "updated_at": utc_to_local(user["updated_at"])
    }


async def add_whitelist(whitelist_data: dict) -> dict:
    """
    Create a new whitelist
    :param whitelist_data: dict
    :return: dict
    """
    try:
        whitelist = await whitelist_collection.insert_one(whitelist_data)
        new_whitelist = await whitelist_collection.find_one({"_id": whitelist.inserted_id})
        return whitelist_helper(new_whitelist)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add whitelist",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def upsert_whitelist(new_whitelists: list[dict], remove_not_exist: bool) -> bool:
    """
    Upsert new whitelist to database
    :param new_whitelists: list
    :return: bool
    """
    try:
        # Get the emails of the new whitelist
        new_emails = {whitelist["email"] for whitelist in new_whitelists}

        # Retrieve current whitelist emails from the database
        current_whitelists = await whitelist_collection.find({}, {"email": 1}).to_list(length=None)
        current_emails = {whitelist["email"]
                          for whitelist in current_whitelists}

        # Determine which emails to delete
        emails_to_delete = current_emails - new_emails

        # Prepare bulk operations
        operations = [
            UpdateOne(
                {"email": whitelist["email"]},
                {"$set": whitelist},
                upsert=True
            ) for whitelist in new_whitelists
        ]
        
        if remove_not_exist:
            # Add delete operations for emails no longer in the new whitelist
            operations.extend(DeleteOne({"email": email})
                            for email in emails_to_delete)
            
            # Downgrade to user role from "aio" to "user"
            downgrade_operations = [UpdateOne(
                {"email": email},
                {"$set": {"role": "user"}}
            ) for email in emails_to_delete]
            
            if downgrade_operations:
                downgrade_result = await user_collection.bulk_write(downgrade_operations)
                logger.info(f"Bulk write downgrade result: {downgrade_result.bulk_api_result}")

        if operations:
            result = await whitelist_collection.bulk_write(operations)
            logger.info(f"Bulk write upgrade result: {result.bulk_api_result}")
        return True
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when upsert whitelist",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def retrieve_all_whitelists() -> list[dict]:
    """
    Retrieve all whitelists in database.
    :return: list
    """
    try:
        whitelists = []
        async for whitelist in whitelist_collection.find():
            whitelists.append(whitelist_helper(whitelist))
        return whitelists
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve whitelists",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_whitelist_by_pipeline(pipeline: list,
                                         page: int,
                                         per_page: int) -> list:
    """
    Retrieve all whitelists with matching search and filter
    :param pipeline: list
    :param page: int
    :param per_page: int
    :return: list
    """
    try:
        pipeline_results = await whitelist_collection.aggregate(pipeline).to_list(length=None)
        whitelists = pipeline_results[0]["whitelists"]
        if len(whitelists) < 1:
            return {
                "whitelists_data": [],
                "total_whitelists": 0,
                "total_pages": 0,
                "current_page": page,
                "per_page": per_page
            }
        total_whitelists = pipeline_results[0]["total"][0]["count"]
        total_pages = (total_whitelists + per_page - 1) // per_page
        result_data = []
        for whitelist in whitelists:
            whitelist_info = whitelist_helper(whitelist)
            result_data.append(whitelist_info)

        return {
            "users_data": result_data,
            "total_whitelists": total_whitelists,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve whitelists",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_whitelist_by_email(email: str) -> dict:
    """
    Retrieve a whitelist with a matching email    
    :param email: str
    :return: dict
    """
    try:
        whitelist = await whitelist_collection.find_one({"email": email})
        if not whitelist:
            raise MessageException("Whitelist not found", 
                                   status.HTTP_404_NOT_FOUND)
        return whitelist_helper(whitelist)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve whitelist",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_whitelist_by_id(id: str, data: dict) -> dict:
    """
    Update a whitelist with a matching id
    :param id: str
    :param data: dict
    :return: dict
    """
    try:
        if len(data) < 1:
            raise MessageException("No data to update", 
                                   status.HTTP_400_BAD_REQUEST)
        current_whitelist = await whitelist_collection.find_one({"_id": ObjectId(id)})
        if not current_whitelist:
            raise Exception("Whitelist not found")
        
        updated = await whitelist_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated.modified_count == 0:
            raise MessageException("Update whitelist failed",
                                   status.HTTP_400_BAD_REQUEST)
        updated_whitelist = await whitelist_collection.find_one({"_id": ObjectId(id)})
        return whitelist_helper(updated_whitelist)
    
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update whitelist",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_whitelist_by_email(email: str) -> bool:
    """
    Delete a whitelist with a matching email
    :param email: str
    :return: bool
    """
    try:
        whitelist_info = await whitelist_collection.find_one({"email": email})
        if not whitelist_info:
            raise MessageException("Whitelist not found", 
                                   status.HTTP_404_NOT_FOUND)
        deleted = await whitelist_collection.delete_one({"email": email})
        if deleted.deleted_count == 0:
            raise MessageException("Delete whitelist failed",
                                   status.HTTP_400_BAD_REQUEST)
    
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete whitelist",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_whitelist_by_id(id: str) -> bool:
    """
    Delete a whitelist with a matching id
    :param email: str
    :return: bool
    """
    try:
        whitelist_info = await whitelist_collection.find_one({"_id": ObjectId(id)})
        if not whitelist_info:
            raise MessageException("Whitelist not found", 
                                   status.HTTP_404_NOT_FOUND)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve whitelist",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)

    async with await mongo_client.start_session() as session:
        try:
            async with session.start_transaction():
                deleted_whitelist = await whitelist_collection.delete_one(
                    {"_id": ObjectId(id)}, session=session)
                
                await user_collection.update_one(
                    {"email": whitelist_info["email"]},
                    {"$set": {"role": "user"}},
                    session=session
                )
        
        except:
            logger.error(f"{traceback.format_exc()}")
            return MessageException("Error when delete whitelist",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            if deleted_whitelist.deleted_count == 0:
                raise MessageException("Delete whitelist failed",
                                       status.HTTP_400_BAD_REQUEST)
            return True
        