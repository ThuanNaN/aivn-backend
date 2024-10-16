import traceback
from app.utils.time import utc_to_local
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_id,
    delete_all_by_exam_id
)
from app.api.v1.controllers.problem import (
    retrieve_problems_by_ids
)
from app.api.v1.controllers.submission import (
    delete_submissions_by_exam_id
)
from app.api.v1.controllers.retake import (
    delete_retakes_by_exam_id
)

logger = Logger("controllers/exam", log_file="exam.log")

try:
    exam_collection = mongo_db["exams"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


#helper
def exam_helper(exam: dict) -> dict:
    return {
        "id": str(exam["_id"]),
        "contest_id": str(exam["contest_id"]),
        "title": exam["title"],
        "description": exam["description"],
        "is_active": exam["is_active"],
        "creator_id": exam["creator_id"],
        "duration": exam["duration"],
        "created_at": utc_to_local(exam["created_at"]),
        "updated_at": utc_to_local(exam["updated_at"])
    }


def update_helper(update_exam_data: dict) -> dict:
    update_exam_data["contest_id"] = ObjectId(update_exam_data["contest_id"])
    return update_exam_data


async def add_exam(exam_data: dict) -> dict:
    """
    Add a new exam to database
    :param exam_data: dict
    :return: dict
    """
    try:
        exam_data["contest_id"] = ObjectId(exam_data["contest_id"])
        exam = await exam_collection.insert_one(exam_data)
        new_exam = await exam_collection.find_one({"_id": exam.inserted_id})
        return exam_helper(new_exam)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_exams() -> list:
    """
    Retrieve all exams from database
    :return: list
    """
    try:
        exams = []
        async for exam in exam_collection.find():
            exams.append(exam_helper(exam))
        return exams
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_exam(id: str) -> dict:
    """
    Retrieve a exam with a matching ID
    :param id: str
    :return: dict
    """
    try:
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if exam:
            return exam_helper(exam)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_exam_detail(id: str) -> dict:
    """
    Retrieve a exam with a matching ID
    :param id: str
    :return: dict
    """
    try:
        exam = await retrieve_exam(id)
        if isinstance(exam, Exception):
            raise exam
        exam_problems = await retrieve_by_exam_id(exam["id"])
        if isinstance(exam_problems, Exception):
            raise exam_problems
        problem_ids = [ObjectId(problem["problem_id"]) for problem in exam_problems]
        
        enriched_problems = await retrieve_problems_by_ids(problem_ids, full_return=True)
        if isinstance(enriched_problems, Exception):
            raise enriched_problems
        
        for exam_problem in exam_problems:
            problem = next((problem for problem in enriched_problems if problem["id"] == exam_problem["problem_id"]), None)
            exam_problem["problem"] = problem if problem else None
        exam_problems_temp = [exam_problem for exam_problem in exam_problems if exam_problem["problem"] is not None]
        exam_problems_temp.sort(key=lambda x: x["index"])
        exam["problems"] = exam_problems_temp
        return exam

    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_exams_by_contest(contest_id: str) -> list:
    """
    Retrieve all exams with a matching contest ID
    :param contest_id: str
    :return: list
    """
    try:
        exams = []
        async for exam in exam_collection.find({"contest_id": ObjectId(contest_id)}):
            exams.append(exam_helper(exam))
        return exams
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
    

async def retrieve_active_exams_by_contest(contest_id: str) -> list:
    """
    Retrieve all active exams with a matching contest ID
    :param contest_id: str
    :return: list
    """
    try:
        exams = []
        async for exam in exam_collection.find({"contest_id": ObjectId(contest_id), "is_active": True}):
            exams.append(exam_helper(exam))
        return exams
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def update_exam(id: str, data: dict) -> bool:
    """
    Update a exam with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise Exception("No data to update")
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if not exam:
            raise Exception("Exam not found")
        update_data = update_helper(data)
        updated_exam = await exam_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )
        if updated_exam.modified_count > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_exam(id: str) -> bool:
    """
    Delete a exam from database
    :param id: str
    :return: bool
    """
    try:
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if not exam:
            raise Exception("Exam not found")
        
        # Delete all exam_problem in exam_problem collection
        deleted_exam_problems = await delete_all_by_exam_id(id)
        if isinstance(deleted_exam_problems, Exception):
            raise deleted_exam_problems
        if not deleted_exam_problems:
            raise Exception("Delete exam_problem failed.")
        
        # Del submissions (del timer, retake)
        deleted_submissions = await delete_submissions_by_exam_id(id)
        if isinstance(deleted_submissions, Exception):
            raise deleted_submissions
        if not deleted_submissions:
            raise Exception("Delete submission failed.")
        
        # Del retakes dont have submission
        deleted_retakes = await delete_retakes_by_exam_id(id)
        if isinstance(deleted_retakes, Exception):
            raise deleted_retakes
        if not deleted_retakes:
            raise Exception("Delete retake failed.")

        # Delete exam in exam collection
        deleted_exam = await exam_collection.delete_one({"_id": ObjectId(id)})
        if deleted_exam.deleted_count == 1:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



async def delete_all_by_contest_id(contest_id: str) -> bool:
    """
    Delete all exams with a matching contest ID
    :param contest_id: str
    :return: bool
    """
    try:
        exams = await retrieve_exams_by_contest(contest_id)
        if isinstance(exams, Exception):
            raise exams
        for exam in exams:
            delete_exam_result = await delete_exam(exam["id"])
            if isinstance(delete_exam_result, Exception):
                raise delete_exam_result
            if not delete_exam_result:
                raise Exception("Delete exam failed")
        return True
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
