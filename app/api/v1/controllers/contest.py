from datetime import datetime
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.exam import (
    retrieve_exam_by_contest,
    delete_all_by_contest_id
)
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_id
)
from app.api.v1.controllers.retake import (
    retrieve_retake_by_user_clerk_id
)

logger = Logger("controllers/contest", log_file="contest.log")

try:
    contest_collection = mongo_db["contests"]
except Exception as e:
    logger.error(f"Error when connect to contest: {e}")
    exit(1)


# helper
def contest_helper(contest) -> dict:
    return {
        "id": str(contest["_id"]),
        "title": contest["title"],
        "description": contest["description"],
        "is_active": contest["is_active"],
        "created_at": str(contest["created_at"]),
        "updated_at": str(contest["updated_at"])
    }

def to_datetime(date_str: str) -> datetime:
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')



async def add_contest(contest_data: dict) -> dict:
    """
    Create a new contest
    :param contest_data: dict
    :return: dict
    """
    try:
        contest = await contest_collection.insert_one(contest_data)
        new_contest = await contest_collection.find_one({"_id": contest.inserted_id})
        return contest_helper(new_contest)
    except Exception as e:
        logger.error(f"Error when add contest: {e}")


async def retrieve_contests() -> list[dict]:
    """
    Retrieve all contests in database
    :return: list[dict]
    """
    try:
        contests = []
        async for contest in contest_collection.find():
            contests.append(contest_helper(contest))
        return contests
    except Exception as e:
        logger.error(f"Error when retrieve contests: {e}")


async def retrieve_available_contests(user_clerk_id: str) -> dict:
    """
    Retrieve all available contests
    :return: list[dict]
    """
    try:
        contests = []
        async for contest in contest_collection.find({"is_active": True}):
            contest_detail = await retrieve_contest_detail(contest["_id"], user_clerk_id)
            if isinstance(contest_detail, Exception):
                raise contest_detail
            contests.append(contest_detail)
        return contests
    except Exception as e:
        logger.error(f"Error when retrieve available contests: {e}")
        return e


async def retrieve_contest(id: str) -> dict:
    """
    Retrieve a contest with a matching ID
    :param contest_id: str
    :return: dict
    """
    try:
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if contest:
            return contest_helper(contest)
    except Exception as e:
        logger.error(f"Error when retrieve contest: {e}")


async def retrieve_contest_detail(id: str, user_clerk_id: str) -> dict:
    """
    Retrieve a contest with a matching contest_id (id),
    including exams with available for user_clerk_id.
    :param id: str
    :return: list
    """
    try:
        contest = await retrieve_contest(id)
        if not contest:
            raise Exception("Contest not found")
        
        retakes = await retrieve_retake_by_user_clerk_id(user_clerk_id)
        if isinstance(retakes, Exception):
            raise retakes
        exam_retake_ids = []
        if retakes:
            exam_retake_ids = [retake["exam_id"] for retake in retakes]
            
        all_exam = await retrieve_exam_by_contest(contest["id"])
        if len(all_exam) < 1:
            raise Exception("Exams not found")
        
        all_exam_detail = []
        retake_exam_detail = []
        for exam in all_exam:
            exam_id = exam["id"]
            exam_problems = await retrieve_by_exam_id(exam_id)
            exam["problems"] = exam_problems
            all_exam_detail.append(exam)

            if exam_id in exam_retake_ids:
                retake_exam_detail.append(exam)

        if len(retake_exam_detail) < 1:
            contest["available_exam"] = all_exam_detail[0]
        elif len(retake_exam_detail) > 1:
            newest_retake = retake_exam_detail[0]
            for retake in retake_exam_detail[1:]:
                if to_datetime(retake["created_at"]) > to_datetime(newest_retake["created_at"]):
                    newest_retake = retake
            contest["available_exam"] = newest_retake
        else:
            contest["available_exam"] = retake_exam_detail[0]

        contest["exams"] = all_exam_detail
        return contest
    except Exception as e:
        logger.error(f"Error when retrieve contest detail: {e}")
        return e


async def update_contest(id: str, data: dict) -> bool:
    """
    Update a contest with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            return False
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise Exception("Contest not found")
        updated_contest = await contest_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if not updated_contest:
            raise Exception("Update contest failed")
        return True
    except Exception as e:
        logger.error(f"Error when update contest: {e}")


async def delete_contest(id: str) -> bool:
    """
    Delete a contest with a matching ID
    :param id: str
    :return: bool
    """
    try:
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise Exception("Contest not found")
        
        deleted_contest = await contest_collection.delete_one({"_id": ObjectId(id)})
        if not deleted_contest:
            raise Exception("Delete contest failed")

        # Delete all exam 
        deleted_exams = await delete_all_by_contest_id(id)
        if not deleted_exams:
            raise Exception("Delete exams failed")

    except Exception as e:
        logger.error(f"Error when delete contest: {e}")

