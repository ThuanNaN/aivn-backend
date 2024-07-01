from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.run_code import test_py_funct
from app.api.v1.controllers.user import retrieve_user

logger = Logger("controllers/submission", log_file="submission.log")

try:
    submission_collection = mongo_db["submissions"]
    setting_collection = mongo_db["setting"]
except Exception as e:
    logger.error(f"Error when connect to submissions: {e}")
    exit(1)


# submission helper
def submission_helper(submission) -> dict:
    return {
        "id": str(submission["_id"]),
        "user_id": submission["user_id"],
        "problems": submission["problems"],
        "created_at": str(submission["created_at"]),
    }

# timer helper


def timer_helper(timer) -> dict:
    return {
        "id": str(timer["_id"]),
        "duration": timer["duration"],
    }

# Create a new submission


async def add_submission(submission_data: dict):
    try:
        submission = await submission_collection.insert_one(submission_data)
        new_submission = await submission_collection.find_one(
            {"_id": submission.inserted_id}
        )
        return submission_helper(new_submission)
    except Exception as e:
        logger.error(f"Error when add submission: {e}")


# Retrieve all submissions
async def retrieve_submissions():
    try:
        submissions = []
        async for submission in submission_collection.find():
            user_info = await retrieve_user(submission["user_id"])
            if not user_info:
                raise Exception(
                    f'User with ID: {submission["user_id"]} not found.')
            return_dict = {
                "username": user_info["username"],
                "email": user_info["email"],
                "avatar": user_info["avatar"],
                **submission_helper(submission)
            }
            submissions.append(return_dict)
        return submissions
    except Exception as e:
        logger.error(f"Error when retrieve submissions: {e}")


async def retrieve_submission(id: str):
    """
    Retrieve a submission with a matching ID
    Args: 
        id: str
    Return:
        dict
    """
    try:
        submission = await submission_collection.find_one({"_id": ObjectId(id)})
        user_info = await retrieve_user(submission["user_id"])
        return_dict = {
            "username": user_info["username"],
            "email": user_info["email"],
            "avatar": user_info["avatar"],
            **submission_helper(submission)
        }
        return return_dict
    except Exception as e:
        logger.error(f"Error when retrieve submission: {e}")


async def retrieve_submission_by_user(user_id: str):
    try:
        submission = await submission_collection.find_one({"user_id": user_id})
        if submission:
            user_info = await retrieve_user(submission["user_id"])
            return_dict = {
                "username": user_info["username"],
                "email": user_info["email"],
                "avatar": user_info["avatar"],
                **submission_helper(submission)
            }
            return return_dict
    except Exception as e:
        logger.error(f"Error retrieve_submission_by_user: {e}")


def run_testcases(code, testcases):
    if not testcases:
        return [], True
    results_dict = test_py_funct(py_func=code,
                                 testcases=testcases,
                                 return_testcase=True,
                                 run_all=True)
    return_dict = []
    is_pass_testcases = True
    for i, result in enumerate(results_dict["testcase_outputs"]):
        return_dict.append(
            {
                "input": testcases[i]["input"],
                "output": str(result["output"]),
                "expected_output": testcases[i]["expected_output"],
                "error": result["error"],
                "is_pass": result["is_pass"]
            }
        )

        if not result["is_pass"]:
            is_pass_testcases = False

    return return_dict, is_pass_testcases


async def add_time_limit(time_data: dict) -> dict:
    """
    Add a new time limit to the database
    Args:
        time_data (dict): time data
    Returns:
        dict: time data
    """
    try:
        time_limit = await setting_collection.insert_one(time_data)
        new_time_limit = await setting_collection.find_one({"_id": time_limit.inserted_id})
        return timer_helper(new_time_limit)
    except Exception as e:
        logger.error(f"Error when add time limit: {e}")


async def retrieve_time_limits() -> list:
    """
    Retrieve all time limits from the database
    Returns:
        list: list of time limits
    """
    try:
        time_limits = []
        async for time_limit in setting_collection.find():
            time_limits.append(timer_helper(time_limit))
        return time_limits
    except Exception as e:
        logger.error(f"Error when retrieve time limits: {e}")


async def retrieve_time_limit(id: str) -> dict:
    """
    Retrieve a time limit from the database
    Args:
        id (str): id of the time limit
    Returns:
        dict: time limit data
    """
    try:
        time_limit = await setting_collection.find_one({"_id": ObjectId(id)})
        if time_limit:
            return timer_helper(time_limit)
    except Exception as e:
        logger.error(f"Error when retrieve time limit: {e}")


async def update_time_limit(id: str, data: dict) -> bool:
    """
    Update a time limit with a matching ID
    Args:
        id (str): time limit ID
        data (dict): time limit data to update
    Returns:
        None
    """
    try:
        time_limit = await setting_collection.find_one({"_id": ObjectId(id)})
        if time_limit:
            updated = await setting_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated:
                return True
            return False
    except Exception as e:
        logger.error(f"Error when update time limit: {e}")
