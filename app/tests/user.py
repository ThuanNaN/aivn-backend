import asyncio
from app.core.database import mongo_db

try:
    user_collection = mongo_db["users"]
except Exception as e:
    print(f"Error when connect to collection: {e}")
    exit(1)


async def missing_field():
    """
    Check if there is any missing field in the user collection
    """
    def check_missing_field(user, fields):
        for field in fields:
            if not field in user:
                return field
        return None

    fields = ['email', 'username', 'role', 'cohort', 'feasible_cohort', 'attend_id']
    all_users = await user_collection.find({}).to_list(length=None)

    for user in all_users:
        missing_field = check_missing_field(user, fields)
        if missing_field:
            print(f"User {user['email']} is missing field: {missing_field}")

    print("All users have all required fields")



async def double_email():
    """
    Check if there is any duplicate email in the user collection
    """
    all_users = await user_collection.find({}).to_list(length=None)
    for user in all_users:
        email = user['email']
        duplicate = await user_collection.find({"email": email}).to_list(length=None)
        if len(duplicate) > 1:
            print(f"Duplicate email: {email}")

    print("No duplicate email")



if __name__ == '__main__':
    asyncio.run(missing_field())
    asyncio.run(double_email())
