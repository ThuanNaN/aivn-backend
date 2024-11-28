import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from app.core.database import mongo_db
from bson.objectid import ObjectId

logger = Logger("controllers/exam_problem", log_file="exam_problem.log")

try:
    exam_problem_collection = mongo_db["exam_problem"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper 
def exam_problem_helper(exam_problem) -> dict:
    return {
        "id": str(exam_problem["_id"]),
        "exam_id": str(exam_problem["exam_id"]),
        "problem_id": str(exam_problem["problem_id"]),
        "index": exam_problem["index"],
        "creator_id": exam_problem["creator_id"],
        "created_at": utc_to_local(exam_problem["created_at"]),
        "updated_at": utc_to_local(exam_problem["updated_at"])
    }

def ObjectId_helper(exam_problem_data: dict) -> dict:
    exam_problem_data["exam_id"] = ObjectId(exam_problem_data["exam_id"])
    exam_problem_data["problem_id"] = ObjectId(exam_problem_data["problem_id"])
    return exam_problem_data


async def add_exam_problem(exam_problem_data: dict) -> dict:
    """
    Add a new exam_problem to database
    :param exam_problem_data: dict
    :return: dict
    """
    try:
        exam_problem_data = ObjectId_helper(exam_problem_data)
        exam_problem = await exam_problem_collection.insert_one(exam_problem_data)
        new_exam_problem = await exam_problem_collection.find_one(
            {"_id": exam_problem.inserted_id}
        )
        return exam_problem_helper(new_exam_problem)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add exam_problem", 
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all exam_problem",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve exam_problem",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_by_exam_problem_id(exam_id: str, problem_id: str) -> dict:
    """
    Retrieve a exam_problem with a matching exam_id and problem_id
    :param exam_id: str
    :param problem_id: str
    :return: dict
    """
    try:
        exam_problem = await exam_problem_collection.find_one(
            {"exam_id": ObjectId(exam_id), "problem_id": ObjectId(problem_id)}
        )
        if exam_problem:
            return exam_problem_helper(exam_problem)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve exam_problem",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_by_exam_id(exam_id: str) -> list:
    """
    Retrieve all exam_problems with a matching exam_id
    :param exam_id: str
    :return: list
    """
    try:
        exam_problems = []
        async for exam_problem in exam_problem_collection.find({"exam_id": ObjectId(exam_id)}):
            exam_problems.append(exam_problem_helper(exam_problem))
        return exam_problems
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve exam_problem",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def update_exam_problem(id: str, data: dict) -> bool | MessageException:
    """
    Update a exam_problem with a matching ID
    :param id: str
    :param data: dict
    """
    try:
        if len(data) < 1:
            raise MessageException("No data provided to update", 
                                   status.HTTP_400_BAD_REQUEST)
        exam_problem = await exam_problem_collection.find_one({"_id": ObjectId(id)})
        if not exam_problem:
            raise MessageException("Exam_problem not found",
                                   status.HTTP_404_NOT_FOUND)
        updated_exam_problem = await exam_problem_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_exam_problem.modified_count == 0:
            raise MessageException("Error when update exam_problem",
                                   status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update exam_problem",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_exam_problem(id: str) -> bool:
    """
    Delete a exam_problem with a matching ID
    :param id: str
    """
    try:
        exam_problem = await exam_problem_collection.find_one({"_id": ObjectId(id)})
        if not exam_problem:
            raise MessageException("Exam_problem not found", 
                                   status.HTTP_404_NOT_FOUND)
        deleted_exam_problem = await exam_problem_collection.delete_one({"_id": ObjectId(id)})
        if deleted_exam_problem.deleted_count == 0:
            raise MessageException("Error when delete exam_problem",
                                   status.HTTP_500_INTERNAL_SERVER_ERROR)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete exam_problem",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
