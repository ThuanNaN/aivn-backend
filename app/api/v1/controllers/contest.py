import traceback
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
        "creator_id": contest["creator_id"], # clerk_user_id
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
        logger.error(f"{traceback.format_exc()}")
        return e



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
        logger.error(f"{traceback.format_exc()}")
        return e



async def retrieve_available_contests(user_clerk_id: str) -> list:
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
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_contest(id: str) -> dict:
    """
    Retrieve a contest with a matching ID
    :param contest_id: str
    :return: dict
    """
    try:
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise Exception("Contest not found")
        return contest_helper(contest)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



async def retrieve_contest_detail(id: str, user_clerk_id: str) -> dict:
    """
    Retrieve a contest with a matching contest_id (id),
    including exams with available for user_clerk_id.
    :param id: str
    :return: list
    """
    try:
        contest = await retrieve_contest(id)
        if isinstance(contest, Exception):
            raise contest

        retakes = await retrieve_retake_by_user_clerk_id(user_clerk_id)
        if isinstance(retakes, Exception):
            raise retakes
        exam_retake_ids = []
        if retakes: # not empty
            exam_retake_ids = [retake["exam_id"] for retake in retakes]
            retake_ids = [retake["id"] for retake in retakes]
            
        all_exam = await retrieve_exam_by_contest(contest["id"])
        if isinstance(all_exam, Exception):
            raise all_exam
        
        all_exam_detail = []
        retake_exam_detail = [] 
        retake_ids_exam = []
        contest["available_exam"] = None
        contest["retake_id"] = None
        if all_exam:
            for exam in all_exam:
                exam_id = exam["id"]
                exam_problems = await retrieve_by_exam_id(exam_id)
                if isinstance(exam_problems, Exception):
                    raise exam_problems
                exam["problems"] = exam_problems
                all_exam_detail.append(exam)

                if exam_id in exam_retake_ids:
                    retake_index = exam_retake_ids.index(exam_id)
                    retake_ids_exam.append(retake_ids[retake_index])
                    retake_exam_detail.append(exam)

            if len(retake_exam_detail) < 1: # no retake exam
                contest["available_exam"] = all_exam_detail[0]

            elif len(retake_exam_detail) > 1: # multiple retake exam
                newest_retake = retake_exam_detail[0]
                newest_retake_index = 0
                for index, retake in enumerate(retake_exam_detail[1:]):
                    if to_datetime(retake["created_at"]) > to_datetime(newest_retake["created_at"]):
                        newest_retake = retake
                        newest_retake_index = index + 1
                contest["available_exam"] = newest_retake
                contest["retake_id"] = retake_ids[newest_retake_index]

            else: # only one retake exam
                contest["available_exam"] = retake_exam_detail[0]
                contest["retake_id"] = retake_ids_exam[0]

        contest["exams"] = all_exam_detail
        return contest
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
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
            raise Exception("No data to update")
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise Exception("Contest not found")
        updated_contest = await contest_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_contest.modified_count == 1:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e



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

        # Delete all exam 
        deleted_exams = await delete_all_by_contest_id(id)
        if isinstance(deleted_exams, Exception):
            raise deleted_exams
        if not deleted_exams:
            raise Exception("Delete exam failed")

        # Delete contest
        deleted_contest = await contest_collection.delete_one({"_id": ObjectId(id)})
        if deleted_contest.deleted_count == 1:
            return True
        return False
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e

