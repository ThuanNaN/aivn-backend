import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from typing import List
from app.core.database import mongo_db
from bson.objectid import ObjectId
from pymongo import UpdateOne, DeleteOne

logger = Logger("controllers/problem_category", log_file="problem_category.log")

try:
    problem_category_collection = mongo_db["problem_category"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper 
def problem_category_helper(problem_category) -> dict:
    return {
        "id": str(problem_category["_id"]),
        "problem_id": str(problem_category["problem_id"]),
        "category_id": str(problem_category["category_id"]),
        "created_at": utc_to_local(problem_category["created_at"]),
        "updated_at": utc_to_local(problem_category["updated_at"])
    }

def ObjectId_helper(problem_category_data: dict) -> dict:
    problem_category_data["problem_id"] = ObjectId(problem_category_data["problem_id"])
    problem_category_data["category_id"] = ObjectId(problem_category_data["category_id"])
    return problem_category_data


async def add_problem_category(problem_category_data: dict) -> dict:
    """
    Add a new problem_category to database
    :param problem_category_data: dict
    :return: dict
    """
    try:
        problem_category_data = ObjectId_helper(problem_category_data)
        problem_category = await problem_category_collection.insert_one(problem_category_data)
        new_problem_category = await problem_category_collection.find_one(
            {"_id": problem_category.inserted_id}
        )
        return problem_category_helper(new_problem_category)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def add_more_problem_category(problem_category_data: List[dict]) -> list:
    """
    Add more problem_category to database
    :param problem_category_data: List[dict]
    :return: list
    """
    try:
        problem_category_data = [ObjectId_helper(problem_category) for problem_category in problem_category_data]
        problem_category = await problem_category_collection.insert_many(problem_category_data)

        new_problem_categories = []
        async for problem_category in problem_category_collection.find(
            {"_id": {"$in": problem_category.inserted_ids}}
        ):
            new_problem_categories.append(problem_category_helper(problem_category))
        return new_problem_categories
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all problem_categories",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_by_problem_category_id(problem_id: str, category_id: str) -> dict:
    """
    Retrieve a exam_problem with a matching ID
    :param problem_id: str
    :param category_id: str
    :return: dict
    """
    try:
        problem_category = await problem_category_collection.find_one(
            {"problem_id": ObjectId(problem_id), "category_id": ObjectId(category_id)}
        )
        if problem_category:
            return problem_category_helper(problem_category)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_by_categories(category_ids: List[str]) -> list:
    """
    Retrieve all problem_category with a matching category_id
    :param category_ids: List[str]
    :return: list
    """
    try:
        problem_categories = []
        category_ids = [ObjectId(category) for category in category_ids]
        async for problem_category in problem_category_collection.find(
            {"category_id": {"$in": category_ids}}
        ):
            problem_categories.append(problem_category_helper(problem_category))
        return problem_categories
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_by_problem_id(problem_id: str) -> list:
    """
    Retrieve all problem_category with a matching problem_id
    :param problem_id: str
    :return: list
    """
    try:
        problem_categories = []
        async for problem_category in problem_category_collection.find(
            {"problem_id": ObjectId(problem_id)}
        ):
            problem_categories.append(problem_category_helper(problem_category))
        return problem_categories
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def upsert_problem_category(problem_id: str, new_problem_categories: list) -> dict:
    """
    Upsert problem_category to database by problem_id
    :param id: str
    :param problem_category_data: dict
    :return: dict
    """
    try:
        new_problem_categories = [ObjectId_helper(problem_category) for problem_category in new_problem_categories]

        current_problem_categories = await problem_category_collection.find(
            {
                "problem_id": ObjectId(problem_id)
            }
        ).to_list(length=None)

        current_categories = {problem_category["category_id"] for problem_category in current_problem_categories}
        new_categories = {problem_category["category_id"] for problem_category in new_problem_categories}

        del_problem_categories = current_categories - new_categories
        operations = [
            UpdateOne(
                {
                    "problem_id": ObjectId(problem_category["problem_id"]),
                    "category_id": ObjectId(problem_category["category_id"])
                },
                {"$set": problem_category},
                upsert=True
            ) for problem_category in new_problem_categories
        ]

        operations.extend(
            DeleteOne(
                {
                    "problem_id": ObjectId(problem_id),
                    "category_id": del_problem_category
                }
            ) for del_problem_category in del_problem_categories
        )
        if operations:
            result = await problem_category_collection.bulk_write(operations)
            logger.info(f"Bulk write result: {result.bulk_api_result}")
        return True

    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when upsert problem_category",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
