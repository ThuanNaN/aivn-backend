from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/exam_problem", log_file="exam_problem.log")

try:
    exam_problem_collection = mongo_db["exam_problem"]
except Exception as e:
    logger.error(f"Error when connect to exam_problem: {e}")
    exit(1)


# helper 
def exam_problem_helper(exam_problem) -> dict:
    return {
        "id": str(exam_problem["_id"]),
        "exam_id": exam_problem["exam_id"],
        "problem_id": exam_problem["problem_id"],
        "index": exam_problem["index"],
        "creator_id": exam_problem["creator_id"],
        "created_at": exam_problem["created_at"],
        "updated_at": exam_problem["updated_at"]
    }


async def add_exam_problem(exam_problem_data: dict) -> dict:
    """
    Add a new exam_problem to database
    :param exam_problem_data: dict
    :return: dict
    """
    try:
        exam_problem = await exam_problem_collection.insert_one(exam_problem_data)
        new_exam_problem = await exam_problem_collection.find_one(
            {"_id": exam_problem.inserted_id}
        )
        return exam_problem_helper(new_exam_problem)
    except Exception as e:
        logger.error(f"Error when add_exam_problem: {e}")


async def retrieve_exam_problems() -> list:
    """
    Retrieve all exam_problems from database
    :return: list 
    """
    try:
        exam_problems = []
        async for exam_problem in exam_problem_collection.find():
            exam_problems.append(exam_problem_helper(exam_problem))
        return exam_problems
    except Exception as e:
        logger.error(f"Error when retrieve exam_problems: {e}")


async def retrieve_exam_problem(id: str) -> dict:
    """
    Retrieve a exam_problem with a matching ID
    :param id: str
    :return: dict
    """
    try:
        exam_problem = await exam_problem_collection.find_one({"_id": ObjectId(id)})
        if exam_problem:
            return exam_problem_helper(exam_problem)
    except Exception as e:
        logger.error(f"Error when retrieve_exam_problem: {e}")


async def update_exam_problem(id: str, data: dict) -> bool:
    """
    Update a exam_problem with a matching ID
    :param id: str
    :param data: dict
    """
    try:
        if len(data) < 1:
            return False
        exam_problem = await exam_problem_collection.find_one({"_id": ObjectId(id)})
        if exam_problem:
            updated_exam_problem = await exam_problem_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated_exam_problem:
                return True
            return False
    except Exception as e:
        logger.error(f"Error when update_exam_problem: {e}")


async def delete_exam_problem(id: str) -> bool:
    """
    Delete a exam_problem with a matching ID
    :param id: str
    """
    try:
        exam_problem = await exam_problem_collection.find_one({"_id": ObjectId(id)})
        if exam_problem:
            await exam_problem_collection.delete_one({"_id": ObjectId(id)})
            return True
    except Exception as e:
        logger.error(f"Error when delete_exam_problem: {e}")