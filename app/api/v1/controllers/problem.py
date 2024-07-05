from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/problem", log_file="problem.log")

try:
    problem_collection = mongo_db["problems"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# helper
def problem_helper(problem) -> dict:
    return {
        "id": str(problem["_id"]),
        "title": problem["title"],
        "description": problem["description"],
        "index": problem["index"],
        "code_template": problem["code_template"],
        "admin_template": problem["admin_template"],
        "public_testcases": problem["public_testcases"],
        "private_testcases": problem["private_testcases"],
        "choices": problem["choices"],
        "created_at": str( problem["created_at"]),
        "updated_at": str(problem["updated_at"])
    }

# helper
def user_problem_helper(problem) -> dict:
    if problem["choices"] is not None:
        for i in range(len(problem["choices"])):
            problem["choices"][i]["is_correct"] = False

    if problem["private_testcases"] is not None:
        problem["private_testcases"] = [{}]

    return {
        "id": str(problem["_id"]),
        "title": problem["title"],
        "description": problem["description"],
        "index": problem["index"],
        "code_template": problem["code_template"],
        "admin_template": problem["admin_template"],
        "public_testcases": problem["public_testcases"],
        "private_testcases": problem["private_testcases"],
        "choices": problem["choices"],
        "created_at": str( problem["created_at"]),
        "updated_at": str(problem["updated_at"])
    }

async def add_problem(problem_data: dict) -> dict:
    """
    Add a new problem to the database
    Args:
        problem_data (dict): problem data
    Returns:
        dict: problem data
    """
    try:
        problem = await problem_collection.insert_one(problem_data)
        new_problem = await problem_collection.find_one({"_id": problem.inserted_id})
        return problem_helper(new_problem)
    except Exception as e:
        logger.error(f"Error when add problem: {e}")


async def retrieve_problems(role: str = None) -> list[dict]:
    """
    Retrieve all problems from the database
    Returns:
        list: list of problems
    """
    try:
        problems = []
        async for problem in problem_collection.find():
            if role == "admin":
                problems.append(problem_helper(problem))
            else:
                problems.append(user_problem_helper(problem))
        return problems
    except Exception as e:
        logger.error(f"Error when retrieve problems: {e}")


async def retrieve_problem(id: str, role: str = None) -> dict:
    """
    Retrieve a problem with a matching ID
    Args:
        id (str): problem ID
    Returns:
        dict: problem data
    """
    try:
        problem = await problem_collection.find_one({"_id": ObjectId(id)})
        if problem:
            if role == "admin":
                return problem_helper(problem)
            else:
                return user_problem_helper(problem)
    except Exception as e:
        logger.error(f"Error when retrieve problem: {e}")


async def update_problem(id: str, data: dict):
    """
    Update a problem with a matching ID
    Args:
        id (str): problem ID
        data (dict): problem data to update
    Returns:
        bool: True if update success, False if not
    """
    try:
        if len(data) < 1:
            return False
        problem = await problem_collection.find_one({"_id": ObjectId(id)})
        if problem:
            updated_problem = await problem_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated_problem:
                return True
            return False
    except Exception as e:
        logger.error(f"Error when update problem: {e}")


async def delete_problem(id: str):
    """
    Delete a problem with a matching ID
    Args:
        id (str): problem ID
    Returns:
        bool: True if delete success, False if not
    """
    try:
        problem = await problem_collection.find_one({"_id": ObjectId(id)})
        if problem:
            await problem_collection.delete_one({"_id": ObjectId(id)})
            return True
    except Exception as e:
        logger.error(f"Error when delete problem: {e}")
