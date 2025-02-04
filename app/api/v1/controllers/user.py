import traceback
import requests
from fastapi import status
from app.core.config import settings
from app.utils import utc_to_local, MessageException, Logger
from requests.exceptions import HTTPError, Timeout
from app.core.database import mongo_client, mongo_db
from pymongo import UpdateOne

logger = Logger("controllers/user", log_file="user.log")

try:
    user_collection = mongo_db["users"]
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
        "cohort": user["cohort"],
        "avatar": user["avatar"],
        "fullname": user["fullname"],
        "bio": user["bio"] if "bio" in user else "",
        "attend_id": user["attend_id"],
        "created_at": utc_to_local(user["created_at"]),
        "updated_at": utc_to_local(user["updated_at"])
    }


def clerk_user_helper(user) -> dict:
    if len(user["email_addresses"]) > 1:
        primary_email_address_id = user["primary_email_address_id"]
        for email_address in user["email_addresses"]:
            if email_address["id"] == primary_email_address_id:
                email = email_address["email_address"]
                break
    else:
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


async def find_missing_attend_id(user_collection) -> str:
    """
    Find the smallest missing attend_id in the user collection
    :param user_collection: collection
    :return: str
    """
    cursor = user_collection.find({}, {"attend_id": 1})
    attend_ids = set()  # Use a set for faster lookup

    async for user in cursor:
        attend_ids.add(user["attend_id"])

    missing_attend_ids = "0".zfill(4)
    while missing_attend_ids in attend_ids:
        missing_attend_ids = str(int(missing_attend_ids) + 1).zfill(4)

    return missing_attend_ids


async def add_user(user_data: dict) -> dict:
    """
    Create a new user
    :param user_data: dict
    :return: dict
    """
    try:
        attend_id = await find_missing_attend_id(user_collection)
        user_data["attend_id"] = attend_id
        user = await user_collection.insert_one(user_data)
        new_user = await user_collection.find_one({"_id": user.inserted_id})
        return user_helper(new_user)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve users",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_user_by_email(email: str) -> dict:
    """
    Retrieve a user with a matching email
    :param email: str
    :return: dict
    """
    try:
        user = await user_collection.find_one({"email": email})
        if not user:
            raise MessageException("User not found", 
                                   status.HTTP_404_NOT_FOUND)
        return user_helper(user)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve admin",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_user(clerk_user_id: str, data: dict) -> bool:
    """
    Update a user with a matching ID
    :param clerk_user_id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise MessageException("No data to update", 
                                   status.HTTP_400_BAD_REQUEST)
        user = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user:
            raise MessageException("User not found",
                                   status.HTTP_404_NOT_FOUND)
    
        updated_user = await user_collection.update_one(
            {"clerk_user_id": clerk_user_id}, {"$set": data}
        )
        if updated_user.modified_count == 0:
            raise MessageException("Update user failed",
                                   status.HTTP_400_BAD_REQUEST)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_user_clerk(clerk_user_id: str) -> dict:
    """
    Retrieve a user data from Clerk
    :param clerk_user_id: str
    :return: dict
    """
    try:
        CLERK_URL = f"https://api.clerk.com/v1/users/{clerk_user_id}"
        CLERK_SECRET_KEY = settings.CLERK_SECRET_KEY
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
        return MessageException("HTTP error occurred",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Timeout as timeout_err:
        logger.error(f"Request timeout: {timeout_err}")
        return MessageException("Request timeout",
                                status.HTTP_408_REQUEST_TIMEOUT)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when upsert admin list",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_user_by_clerk_user_id(clerk_user_id: str) -> bool:
    """
    Delete a user with a matching clerk_user_id
    :param clerk_user_id: str
    :return: bool
    """
    try:
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user_info:
            raise MessageException("User not found", status.HTTP_404_NOT_FOUND)
        
        # Check if user is in other collections
        # 1. Problem: creator_id
        problems = await mongo_db["problems"].find({"creator_id": clerk_user_id}).to_list(length=None)
        if problems:
            raise MessageException("User is a creator of some problems", status.HTTP_400_BAD_REQUEST)
        
        # 2. Exam: creator_id
        exams = await mongo_db["exams"].find({"creator_id": clerk_user_id}).to_list(length=None)
        if exams:
            raise MessageException("User is a creator of some exams", status.HTTP_400_BAD_REQUEST)
        
        # 3. Problem-Exam: creator_id
        problem_exams = await mongo_db["problem_exams"].find({"creator_id": clerk_user_id}).to_list(length=None)
        if problem_exams:
            raise MessageException("User is a creator of some problem-exams", status.HTTP_400_BAD_REQUEST)
        
        # 4. Contest: creator_id
        contests = await mongo_db["contests"].find({"creator_id": clerk_user_id}).to_list(length=None)
        if contests:
            raise MessageException("User is a creator of some contests", status.HTTP_400_BAD_REQUEST)

        # 5. Meeting: creator_id
        meetings = await mongo_db["meetings"].find({"creator_id": clerk_user_id}).to_list(length=None)
        if meetings:
            raise MessageException("User is a creator of some meetings", status.HTTP_400_BAD_REQUEST)
        
        # 6. Document: creator_id
        documents = await mongo_db["documents"].find({"creator_id": clerk_user_id}).to_list(length=None)
        if documents:
            raise MessageException("User is a creator of some documents", status.HTTP_400_BAD_REQUEST)
        
        # 7. Submission: clerk_user_id
        submissions = await mongo_db["submissions"].find({"clerk_user_id": clerk_user_id}).to_list(length=None)
        if submissions:
            raise MessageException("User is a creator of some submissions", status.HTTP_400_BAD_REQUEST)
        
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete user",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
                                
    
    async with await mongo_client.start_session() as session:
        try:
            async with session.start_transaction():
                # Del attendees
                await mongo_db["attendees"].delete_many(
                    {"attend_id": user_info["attend_id"]}, session=session)

                # Delete user
                deleted_user = await user_collection.delete_one(
                    {"clerk_user_id": clerk_user_id}, session=session)
                
        except:
            logger.error(f"{traceback.format_exc()}")
            return MessageException("Error when delete user",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            if deleted_user.deleted_count == 0:
                raise MessageException("Delete user failed",
                                       status.HTTP_400_BAD_REQUEST)
            return True
        