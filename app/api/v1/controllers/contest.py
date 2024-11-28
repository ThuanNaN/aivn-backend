import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from app.core.database import mongo_db
from bson.objectid import ObjectId
from app.api.v1.controllers.exam import (
    retrieve_exams_by_contest,
    delete_all_by_contest_id
)
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_id
)
from app.api.v1.controllers.retake import (
    retrieve_retakes_by_user_exam_id
)

logger = Logger("controllers/contest", log_file="contest.log")

try:
    contest_collection = mongo_db["contests"]
    exam_collection = mongo_db["exams"]
    user_collection = mongo_db["users"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper
def contest_helper(contest) -> dict:
    return {
        "id": str(contest["_id"]),
        "title": contest["title"],
        "description": contest["description"],
        "instruction": contest["instruction"],
        "is_active": contest["is_active"],
        "cohorts": contest["cohorts"],
        "certificate_template": contest["certificate_template"],
        "creator_id": contest["creator_id"],
        "slug": contest["slug"],
        "created_at": utc_to_local(contest["created_at"]),
        "updated_at": utc_to_local(contest["updated_at"])
    }


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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contests",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_available_contests(clerk_user_id: str) -> list | MessageException:
    """
    Retrieve all available contests
    :return: list[dict]
    """
    try:
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        pipeline = [
            {
                "$match": {
                    "is_active": True,
                    "$or": [
                        { "cohorts": { "$exists": False } },
                        { "cohorts": None },
                        { "cohorts": { "$lte": user_info["cohort"] } }
                    ]
                }
            }
        ]
        result = await contest_collection.aggregate(pipeline).to_list(length=None)

        contests = []
        for contest in result:
            contest_detail = await retrieve_contest_detail(contest["_id"], clerk_user_id)
            contests.append(contest_detail)
        return contests
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contests",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_contest(id: str) -> dict:
    """
    Retrieve a contest with a matching ID
    :param contest_id: str
    :return: dict
    """
    try:
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        return contest_helper(contest)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_contest_by_slug(slug: str) -> dict:
    """
    Retrieve a contest with a matching slug
    :param slug: str
    :return: dict
    """
    try:
        contest = await contest_collection.find_one({"slug": slug})
        if not contest:
             raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        return contest_helper(contest)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_contest_detail(id: str, clerk_user_id: str) -> dict:
    """
    Retrieve a contest with a matching contest_id (id),
    including exams with available for clerk_user_id.
    :param id: str
    :return: list
    """
    try:
        contest = await retrieve_contest(id)
        if isinstance(contest, MessageException):
            return contest
        all_exam = await retrieve_exams_by_contest(contest["id"])
        if isinstance(all_exam, MessageException):
            return all_exam
        
        if not all_exam:
            contest["available_exam"] = None
            contest["retake_id"] = None
            contest["exams"] = []
            return contest
            
        all_exam_detail = []
        retake_info = []
        for exam in all_exam:

            exam_id = exam["id"]
            exam_problems = await retrieve_by_exam_id(exam_id)

            exam["problems"] = exam_problems
            all_exam_detail.append(exam)

            retakes = await retrieve_retakes_by_user_exam_id(clerk_user_id, exam_id)
            retake_info.extend(retakes)

        contest["exams"] = all_exam_detail
        # Exist retake
        if retake_info: 
            newest_retake = max(retake_info, key=lambda x: x["created_at"])
            newest_exam_id = newest_retake["exam_id"]
            contest["available_exam"] = next((exam for exam in all_exam_detail if exam["id"] == newest_exam_id), None)
            contest["retake_id"] = newest_retake["id"]
        # No retake
        else: 
            contest["retake_id"] = None
            contest["available_exam"] = all_exam_detail[0]

        return contest
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contest detail",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_contest(id: str, data: dict) -> bool:
    """
    Update a contest with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise MessageException("No data to update", 
                                   status.HTTP_400_BAD_REQUEST)
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        updated_contest = await contest_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_contest.modified_count == 0:
            raise MessageException("Update contest failed", 
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_contest(id: str) -> bool:
    """
    Delete a contest with a matching ID
    :param id: str
    :return: bool
    """
    try:
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        
        all_exam = await exam_collection.find({"contest_id": ObjectId(id)}).to_list(length=None)
        if len(all_exam) > 0:
            await delete_all_by_contest_id(id)

        deleted_contest = await contest_collection.delete_one({"_id": ObjectId(id)})
        if deleted_contest.deleted_count == 0:
            raise MessageException("Delete contest failed", 
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
