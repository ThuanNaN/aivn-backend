import traceback
import os
import requests
from app.utils.time import utc_to_local
from requests.exceptions import HTTPError, Timeout
from app.core.database import mongo_db
from app.utils.logger import Logger
from pymongo import UpdateOne, DeleteOne, InsertOne

logger = Logger("controllers/user", log_file="user.log")

try:
    user_collection = mongo_db["users"]
    whitelist_collection = mongo_db["whitelists"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# helper
def user_helper(user) -> dict:
    if "fullname" not in user or user["fullname"] == "":
        user["fullname"] = user["username"]
    return {
        "id": str(user["_id"]),
        "clerk_user_id": user["clerk_user_id"],
        "email": user["email"],
        "username": user["username"],
        "role": user["role"],
        "avatar": user["avatar"],
        "fullname": user["fullname"],
        "bio": user["bio"] if "bio" in user else "",
        "attend_id": user["attend_id"],
        "created_at": utc_to_local(user["created_at"]),
        "updated_at": utc_to_local(user["updated_at"])
    }


def clerk_user_helper(user) -> dict:
    email = user["email_addresses"][0]["email_address"]
    if user["username"] is None:
        if user["first_name"] is not None and user["last_name"] is not None:
            username = user["first_name"] + " " + user["last_name"]
        else:
            username = email.split("@")[0]
    else:
        username = user["username"]

    if user["image_url"] is None:
        image_url = "https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.facebook.com%2Faivietnam.edu.vn%2F&psig=AOvVaw1Y_V6Js0AFy7P34aNqjBn3&ust=1719491806171000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCPiK8qOk-YYDFQAAAAAdAAAAABAE"
    else:
        image_url = user["image_url"]

    return {
        "id": user["id"],
        "clerk_user_id": user["id"],
        "username": username,
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "avatar": image_url,
        "email": email
    }


def whitelist_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "nickname": user["nickname"],
    }


async def add_user(user_data: dict) -> dict:
    """
    Create a new user
    :param user_data: dict
    :return: dict
    """
    try:
        all_user = await user_collection.find().to_list(length=None)
        attend_id = str(len(all_user)).zfill(4)
        user_data["attend_id"] = attend_id
        user = await user_collection.insert_one(user_data)
        new_user = await user_collection.find_one({"_id": user.inserted_id})
        return user_helper(new_user)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_users() -> list[dict]:
    """
    Retrieve all users in database
    :return: list
    """
    try:
        users = []
        async for user in user_collection.find():
            users.append(user_helper(user))
        return users
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_user(clerk_user_id: str) -> dict:
    """
    Retrieve a user with a matching ID
    :param clerk_user_id: str
    :return: dict
    """
    try:
        user = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if user:
            return user_helper(user)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_user_by_email(email: str) -> dict:
    """
    Retrieve a user with a matching email
    :param email: str
    :return: dict
    """
    try:
        user = await user_collection.find_one({"email": email})
        if user:
            return user_helper(user)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_admin_users() -> list[dict]:
    """
    Retrieve all admin users in database
    :return: list
    """
    try:
        admins = []
        async for admin in user_collection.find({"role": "admin"}):
            admins.append(user_helper(admin))
        return admins
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_user_by_pipeline(pipeline: list,
                                            page: int,
                                            per_page: int) -> dict:
    """
    Retrieve users with search filter and pagination
    :param pipeline: list
    :param page: int
    :param per_page: int
    :return: dict
    """
    try:
        pipeline_results = await user_collection.aggregate(pipeline).to_list(length=None)
        users = pipeline_results[0]["users"]
        if len(users) < 1:
            return {
                "users_data": [],
                "total_users": 0,
                "total_pages": 0,
                "current_page": page,
                "per_page": per_page
            }
        total_users = pipeline_results[0]["total"][0]["count"]
        total_pages = (total_users + per_page - 1) // per_page
        result_data = []
        for user in users:
            user_info = user_helper(user)
            result_data.append(user_info)

        return {
            "users_data": result_data,
            "total_users": total_users,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def update_user(clerk_user_id: str, data: dict) -> bool:
    """
    Update a user with a matching ID
    :param clerk_user_id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise Exception("No data to update")
        user = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user:
            raise Exception("User not found")
    
        updated_user = await user_collection.update_one(
            {"clerk_user_id": clerk_user_id}, {"$set": data}
        )
        if updated_user.modified_count > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_user_clerk(clerk_user_id: str) -> dict:
    """
    Retrieve a user data from Clerk
    :param clerk_user_id: str
    :return: dict
    """
    try:
        CLERK_URL = f"https://api.clerk.com/v1/users/{clerk_user_id}"
        CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
        headers = {
            'Authorization': f'Bearer {CLERK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.get(CLERK_URL, headers=headers, timeout=10)
        response.raise_for_status()
        user_data = response.json()

        return clerk_user_helper(user_data)

    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Timeout as timeout_err:
        logger.error(f"Request timeout: {timeout_err}")
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



async def add_whitelist_via_file(whitelist_data: list[dict]) -> dict:
    """
    Create a new whitelist
    :param whitelist_data: list
    :return: dict
    """
    try:
        operations = [InsertOne(data) for data in whitelist_data]
        result = await whitelist_collection.bulk_write(operations)
        inserted_count = result.inserted_count
        logger.info(f"Number of documents inserted: {inserted_count}")
        return {"inserted_count": inserted_count}
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_whitelists() -> list[dict]:
    """
    Retrieve all whitelists in database.
    :return: list
    """
    try:
        whitelists = []
        async for whitelist in whitelist_collection.find():
            whitelists.append(whitelist_helper(whitelist))
        return whitelists
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def check_whitelist_via_email(email: str) -> bool:
    """
    Check an email is in whitelist by email.
    :param email: str
    :return: bool
    """
    try:
        whitelist = await whitelist_collection.find_one({"email": email})
        if whitelist:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def check_whitelist_via_id(clerk_user_id: str) -> bool:
    """
    Check an email is in whitelist by clerk_user_id
    Only use for user who has been logged in before -> exist in users collection
    :param clerk_user_id: str
    :return: bool
    """
    try:
        user_data = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if user_data:
            email = user_data["email"]
            whitelist = await whitelist_collection.find_one({"email": email})
            if whitelist:
                return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def upsert_whitelist(new_whitelists: list[dict]) -> bool:
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

        # Add delete operations for emails no longer in the new whitelist
        operations.extend(DeleteOne({"email": email})
                          for email in emails_to_delete)

        if operations:
            result = await whitelist_collection.bulk_write(operations)
            logger.info(f"Bulk write result: {result.bulk_api_result}")
        return True
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def upsert_admin_list(new_admins: list[dict]) -> bool:
    """
    Upsert new admin list to users collection via matching email.
    If the user with match email, update the role to admin if not already.
    The others user with not in admin list, update to role aio.
    :param new_admins: list
    :return: bool
    """
    try:
        # Get the emails of the new admin list
        new_admin_emails = {admin["email"] for admin in new_admins}

        # Retrieve current admin emails from the database
        current_admins = await user_collection.find({"role": "admin"}, {"email": 1}).to_list(length=None)
        current_admin_emails = {admin["email"] for admin in current_admins}

        # Determine which emails to update

        # user/aio -> admin
        emails_to_upgrade = new_admin_emails - current_admin_emails

        # admin -> aio
        emails_to_downgrade = current_admin_emails - new_admin_emails

        # Prepare bulk operations
        operations = []

        # Upgrade phase
        for admin in new_admins:
            if admin["email"] in emails_to_upgrade:
                operations.append(
                    UpdateOne(
                        {"email": admin["email"]},
                        {"$set": {"role": "admin"}}
                    )
                )
        # Downgrade phase
        for admin in current_admins:
            if admin["email"] in emails_to_downgrade:
                operations.append(
                    UpdateOne(
                        {"email": admin["email"]},
                        {"$set": {"role": "aio"}}
                    )
                )
        if operations:
            result = await user_collection.bulk_write(operations)
            logger.info(f"Bulk write result: {result.bulk_api_result}")
        return True
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_whitelist_by_email(email: str) -> bool:
    """
    Delete a whitelist with a matching email
    :param email: str
    :return: bool
    """
    try:
        deleted = await whitelist_collection.delete_one({"email": email})
        if deleted.deleted_count > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_user_by_clerk_user_id(clerk_user_id: str) -> bool:
    """
    Delete a user with a matching clerk_user_id
    :param clerk_user_id: str
    :return: bool
    """
    try:
        deleted = await user_collection.delete_one({"clerk_user_id": clerk_user_id})
        if deleted.deleted_count > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e