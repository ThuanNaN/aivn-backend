from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.exam import (
    retrieve_exam_by_contest,
)
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_id,
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


async def retrieve_contest_detail(id: str):
    """
    Retrieve a contest with a matching ID, including exams
    :param id: str
    :return: list
    """
    try:
        results = []
        contest = await retrieve_contest(id)
        if contest:
            exams = await retrieve_exam_by_contest(contest["id"])
            for exam in exams:
                problems = await retrieve_by_exam_id(exam["id"])
                exam["problems"] = problems
                results.append(exam)
        contest["exams"] = results
        return contest
    except Exception as e:
        logger.error(f"Error when retrieve contest detail: {e}")


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
        if contest:
            updated_contest = await contest_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated_contest:
                return True
            return False
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
        if contest:
            await contest_collection.delete_one({"_id": ObjectId(id)})
            return True
    except Exception as e:
        logger.error(f"Error when delete contest: {e}")

