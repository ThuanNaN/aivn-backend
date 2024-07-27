import asyncio
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.category import (
    category_helper
)
from app.api.v1.controllers.problem_category import (
    delete_all_by_problem_id
)

logger = Logger("controllers/problem", log_file="problem.log")

try:
    problem_collection = mongo_db["problems"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper (admin)
def problem_helper(problem) -> dict:
    return {
        "id": str(problem["_id"]),
        "creator_id": problem["creator_id"],
        "title": problem["title"],
        "description": problem["description"],
        "slug": problem["slug"],
        "difficulty": problem["difficulty"],
        "is_published": problem["is_published"],
        "admin_template": problem["admin_template"],
        "code_template": problem["code_template"],
        "code_solution": problem["code_solution"],
        "public_testcases": problem["public_testcases"],
        "private_testcases": problem["private_testcases"],
        "choices": problem["choices"],
        "created_at": str( problem["created_at"]),
        "updated_at": str(problem["updated_at"])
    }

# helper (user)
def hide_problem_helper(problem) -> dict:
    if problem["choices"] is not None:
        for i in range(len(problem["choices"])):
            problem["choices"][i]["is_correct"] = False

    if problem["private_testcases"] is not None:
        problem["private_testcases"] = []

    return {
        "id": str(problem["_id"]),
        "creator_id": problem["creator_id"],
        "title": problem["title"],
        "description": problem["description"],
        "slug": problem["slug"],
        "difficulty": problem["difficulty"],
        "is_published": problem["is_published"],
        "admin_template": problem["admin_template"],
        "code_template": problem["code_template"],
        "code_solution": "",
        "public_testcases": problem["public_testcases"],
        "private_testcases": problem["private_testcases"],
        "choices": problem["choices"],
        "created_at": str( problem["created_at"]),
        "updated_at": str(problem["updated_at"]),
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


async def retrieve_problems(full_return: bool = False) -> list:
    """
    Retrieve all problems from the database
    :param full_return: bool
    :return: list
    """
    try:
        problems = []
        async for problem in problem_collection.find():
            if full_return:
                problem_data = problem_helper(problem)
            else:
                problem_data = hide_problem_helper(problem)
            problems.append(problem_data)
        return problems
    except Exception as e:
        logger.error(f"Error when retrieve problems: {e}")


async def retrieve_problems_by_ids(ids: list, full_return: bool = False) -> list:
    """
    Retrieve problems with a matching IDs
    :param ids: list
    :param full_return: bool
    :return: list
    """
    try:
        problems = []
        async for problem in problem_collection.find({"_id": {"$in": ids}}):
            if full_return:
                problem_data = problem_helper(problem)
            else:
                problem_data = hide_problem_helper(problem)
            problems.append(problem_data)
        return problems
    except Exception as e:
        logger.error(f"Error when retrieve problems: {e}")


async def retrieve_problem(id: str, full_return: bool = False) -> dict:
    """
    Retrieve a problem with a matching ID
    :param id: str
    :param full_return: bool
    :return: dict
    """
    try:
        problem = await problem_collection.find_one({"_id": ObjectId(id)})
        if problem:
            if full_return:
                return problem_helper(problem)
            else:
                return hide_problem_helper(problem)
    except Exception as e:
        logger.error(f"Error when retrieve problem: {e}")


async def retrieve_search_filter_pagination(pipeline: list,
                                            page: int,
                                            per_page: int, 
                                            ) -> dict:
    """
    Retrieve all problems with search, filter and pagination.
    :param pipeline: list
    :param page: int
    :param per_page: int
    :return: dict
    """
    try:
        pipeline_results = await problem_collection.aggregate(pipeline).to_list(length=None)
        problems = pipeline_results[0]["problems"]
        if len(problems) < 1:
            return {
                "problems_data": [],
                "total_problems": 0,
                "total_pages": 0,
                "current_page": page,
                "per_page": per_page
            }

        total_problems = pipeline_results[0]["total"][0]["count"]
        total_pages = (total_problems + per_page - 1) // per_page

        result_data = []
        for problem in problems:  
            problem_info = hide_problem_helper(problem)
            return_dict = {
                **problem_info,
                "categories": [category_helper(category) for category in problem["category_info"]]
            }
            result_data.append(return_dict)
        return {
            "problems_data": result_data,
            "total_problems": total_problems,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"Error when retrieve problems with search, filter and pagination: {e}")


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
        if not problem:
            raise Exception("Problem not found")
        
        deleted_problem = await problem_collection.delete_one({"_id": ObjectId(id)})
        if not deleted_problem:
            raise Exception("Error when delete problem")

        # Delete in problem_category collection
        deleted_problem_category = await delete_all_by_problem_id(id)
        if not deleted_problem_category:
            raise Exception("Error when delete problem_category")

        return True
    except Exception as e:
        logger.error(f"Error when delete problem: {e}")
