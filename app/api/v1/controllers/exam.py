import traceback
from app.utils import (
    MessageException,
    Logger,
    utc_to_local
)
from fastapi import status
from app.core.database import mongo_client, mongo_db
from bson.objectid import ObjectId
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_id,
)
from app.api.v1.controllers.problem import (
    retrieve_problems_by_ids
)
from app.api.v1.controllers.cohort_permission import is_contest_permission


logger = Logger("controllers/exam", log_file="exam.log")

try:
    user_collection = mongo_db["users"]
    contest_collection = mongo_db["contests"]
    exam_collection = mongo_db["exams"]
    exam_problem_collection = mongo_db["exam_problem"]
    submission_collection = mongo_db["submissions"]
    retake_collection = mongo_db["retake"]
    timer_collection = mongo_db["timer"]
    certificate_collection = mongo_db["certificate"]
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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add exam", 
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all exams",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_exam(id: str, clerk_user_id: str) -> dict | MessageException:
    """
    Retrieve a exam with a matching ID
    :param id: str
    :return: dict
    """
    try:
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if not exam:
            raise MessageException("Exam not found", 
                                   status.HTTP_404_NOT_FOUND)
        permission = await is_contest_permission(exam["contest_id"], clerk_user_id)
        if isinstance(permission, MessageException):
            return permission
        if not permission:
            raise MessageException("You are not allowed to access this exam",
                                   status.HTTP_403_FORBIDDEN)
        return exam_helper(exam)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve exam",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_exam_detail(id: str, clerk_user_id: str) -> dict | MessageException:
    """
    Retrieve a exam with a matching ID
    :param id: str
    :return: dict
    """
    try:
        exam = await retrieve_exam(id, clerk_user_id)
        if isinstance(exam, MessageException):
            return exam
        
        exam_problems = await retrieve_by_exam_id(exam["id"])
        if isinstance(exam_problems, MessageException):
            return exam_problems
        
        problem_ids = [ObjectId(problem["problem_id"]) for problem in exam_problems]
        enriched_problems = await retrieve_problems_by_ids(problem_ids, full_return=True)
        for exam_problem in exam_problems:
            problem = next((problem for problem in enriched_problems if problem["id"] == exam_problem["problem_id"]), None)
            exam_problem["problem"] = problem if problem else None
        exam_problems_temp = [exam_problem for exam_problem in exam_problems if exam_problem["problem"] is not None]
        exam_problems_temp.sort(key=lambda x: x["index"])
        exam["problems"] = exam_problems_temp
        return exam
    
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve exam detail",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all exams",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve all exams",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_exam(id: str, data: dict) -> bool | MessageException:
    """
    Update a exam with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise MessageException("No data to update", 
                                   status.HTTP_400_BAD_REQUEST)
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if not exam:
            raise MessageException("Exam not found",
                                   status.HTTP_404_NOT_FOUND)
        update_data = update_helper(data)
        updated_exam = await exam_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_data}
        )
        if updated_exam.modified_count == 0:
            raise MessageException("Error when update exam",
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update exam",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_exam(id: str) -> bool | MessageException:
    """
    Delete a exam from database
    :param id: str
    :return: bool
    """
    try:
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if not exam:
            raise MessageException("Exam not found",
                                   status.HTTP_404_NOT_FOUND)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete exam",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)

    async with await mongo_client.start_session() as session:
        try:
            async with session.start_transaction():
                # Delete all exam_problem in exam_problem collection
                await exam_problem_collection.delete_many({"exam_id": ObjectId(id)}, session=session)
                logger.info(f"Deleted all exam_problems")

                # Del all retakes by exam_id
                await retake_collection.delete_many({"exam_id": ObjectId(id)}, session=session)
                logger.info(f"Deleted all retakes")

                # Del all timer by exam_id
                await timer_collection.delete_many({"exam_id": ObjectId(id)}, session=session)

                # Del all certificates by 
                submission_ids = []
                async for submission in submission_collection.find({"exam_id": ObjectId(id)}):
                    submission_ids.append(submission["_id"])
                await certificate_collection.delete_many({"submission_id": {"$in": submission_ids}}, session=session)

                # Del submissions by exam_id
                await submission_collection.delete_many({"exam_id": ObjectId(id)}, session=session)
                logger.info(f"Deleted all submissions")

                # Delete exam in exam collection
                await exam_collection.delete_one({"_id": ObjectId(id)}, session=session) 
                logger.info(f"Deleted exam with ID: {id}")
        
        except:
            logger.error(f"{traceback.format_exc()}")
            return MessageException("Error when delete exam",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return True


async def delete_all_by_contest_id(contest_id: str) -> bool:
    """
    Delete all exams with a matching contest ID
    :param contest_id: str
    :return: bool
    """
    try:
        exams = await retrieve_exams_by_contest(contest_id)
        for exam in exams:
            await delete_exam(exam["id"])
        return True
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete all exams",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)

