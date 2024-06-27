import os
import requests
from requests.exceptions import HTTPError, Timeout
from app.core.database import mongo_db
from app.utils.logger import Logger


logger = Logger("controllers/user", log_file="user.log")

try:
    user_collection = mongo_db["users"]
    whitelist_collection = mongo_db["whitelists"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# helper


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "clerk_user_id": user["clerk_user_id"],
        "email": user["email"],
        "username": user["username"],
        "role": user["role"],
        "avatar": user["avatar"],
        "created_at": str(user["created_at"]),
        "updated_at": str(user["updated_at"])
    }

def clerk_user_helper(user) -> dict:
    if user["username"] is None:
        username = user["first_name"] + " " + user["last_name"]
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
        "email": user["email_addresses"][0]["email_address"],
    }

def whitelist_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "nickname": user["nickname"],
    }


# Create a new user
async def add_user(user_data: dict) -> dict:
    try:
        user = await user_collection.insert_one(user_data)
        new_user = await user_collection.find_one({"_id": user.inserted_id})
        return user_helper(new_user)
    except Exception as e:
        logger.error(f"Error when add user: {e}")


# Retrieve all users
async def retrieve_users() -> list[dict]:
    try:
        users = []
        async for user in user_collection.find():
            users.append(user_helper(user))
        return users
    except Exception as e:
        logger.error(f"Error when retrieve users: {e}")


# Retrieve a user with a matching ID
async def retrieve_user(clerk_user_id: str) -> dict:
    try:
        user = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if user:
            return user_helper(user)
    except Exception as e:
        logger.error(f"Error when retrieve user: {e}")


# Update a user with a matching ID
async def update_user(clerk_user_id: str, data: dict):
    try:
        if len(data) < 1:
            return False
        user = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if user:
            updated_user = await user_collection.update_one(
                {"clerk_user_id": clerk_user_id}, {"$set": data}
            )
            if updated_user:
                return True
            return False
    except Exception as e:
        logger.error(f"Error when update user: {e}")


# Retrieve a user data from Clerk
async def retrieve_user_clerk(clerk_user_id: str) -> dict:
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
        logger.error(f"Error when retrieve user: {e}")



# Create a new whitelist
async def add_whitelist(whitelist_data: dict) -> dict:
    try:
        whitelist = await whitelist_collection.insert_one(whitelist_data)
        new_whitelist = await whitelist_collection.find_one({"_id": whitelist.inserted_id})
        return whitelist_helper(new_whitelist)
    except Exception as e:
        logger.error(f"Error when add whitelist: {e}")


# Retrieve all whitelists
async def retrieve_whitelists():
    try:
        whitelists = []
        async for whitelist in whitelist_collection.find():
            whitelists.append(whitelist_helper(whitelist))
        return whitelists
    except Exception as e:
        logger.error(f"Error when retrieve whitelists: {e}")


# Check an email is in whitelist
async def check_whitelist(email: str) -> bool:
    try:
        whitelist = await whitelist_collection.find_one({"email": email})
        if whitelist:
            return True
    except Exception as e:
        logger.error(f"Error when check whitelist: {e}")