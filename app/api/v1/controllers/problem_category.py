from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/problem_category", log_file="problem_category.log")

try:
    problem_category_collection = mongo_db["problem_category"]
except Exception as e:
    logger.error(f"Error when connect to problem_category: {e}")
    exit(1)


# helper 
def problem_category_helper(exam_problem) -> dict:
    return {
        "id": str(exam_problem["_id"]),
        "problem_id": exam_problem["problem_id"],
        "category_id": exam_problem["category_id"],
        "created_at": exam_problem["created_at"],
        "updated_at": exam_problem["updated_at"]
    }


async def add_problem_category(problem_category_data: dict) -> dict:
    """
    Add a new add_problem_category to database
    :param problem_category_data: dict
    :return: dict
    """
    try:
        problem_category = await problem_category_collection.insert_one(problem_category_data)
        new_problem_category = await problem_category_collection.find_one(
            {"_id": problem_category.inserted_id}
        )
        return problem_category_helper(new_problem_category)
    except Exception as e:
        logger.error(f"Error when add_problem_category: {e}")


async def retrieve_problem_categories() -> list:
    """
    Retrieve all problem_categories
    :return: list
    """
    problem_categories = []
    try:
        async for problem_category in problem_category_collection.find():
            problem_categories.append(problem_category_helper(problem_category))
        return problem_categories
    except Exception as e:
        logger.error(f"Error when retrieve_problem_categories: {e}")


async def retrieve_by_id(id: str) -> dict:
    """
    Retrieve a problem_category with a matching ID
    :param id: str
    :return: dict
    """
    try:
        problem_category = await problem_category_collection.find_one(
            {"_id": ObjectId(id)}
        )
        if problem_category:
            return problem_category_helper(problem_category)
    except Exception as e:
        logger.error(f"Error when retrieve_by_id: {e}")


async def retrieve_by_problem_category_id(problem_id: str, category_id: str) -> dict:
    """
    Retrieve a exam_problem with a matching ID
    :param problem_id: str
    :param category_id: str
    :return: dict
    """
    try:
        problem_category = await problem_category_collection.find_one(
            {"problem_id": problem_id, "category_id": category_id}
        )
        if problem_category:
            return problem_category_helper(problem_category)
    except Exception as e:
        logger.error(f"Error when retrieve_by_problem_category_id: {e}")


async def delete_problem_category(id: str) -> bool:
    """
    Delete a delete_problem_category with a matching ID
    :param id: str
    """
    try:
        delete = await problem_category_collection.delete_one({"_id": ObjectId(id)})
        if delete:
            return True
        return False
    except Exception as e:
        logger.error(f"Error when delete_problem_category: {e}")
