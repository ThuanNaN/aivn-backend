import traceback
from app.utils.time import utc_to_local, is_past
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/meeting", log_file="meeting.log")
try:
    meeting_collection = mongo_db["meetings"]
except Exception as e:
    logger.error(f"Error when connect to exam: {e}")
    exit(1)


# helper
def meeting_helper(meeting: dict) -> dict:
    return {
        "id": str(meeting["_id"]),
        "title": meeting["title"],
        "description": meeting["description"],
        "lecturer": meeting["lecturer"],
        "date": utc_to_local(meeting["date"]),
        "start_time": utc_to_local(meeting["start_time"]),
        "end_time": utc_to_local(meeting["end_time"]),
        "created_at": utc_to_local(meeting["created_at"]),
        "updated_at": utc_to_local(meeting["updated_at"])
    }


async def add_meeting(meeting_data: dict) -> dict:
    """
    Add a new meeting to database
    :param meeting_data: dict
    :return: dict
    """
    try:
        meeting = await meeting_collection.insert_one(meeting_data)
        new_meeting = await meeting_collection.find_one({"_id": meeting.inserted_id})
        return meeting_helper(new_meeting)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
    

async def retrieve_meetings() -> list:
    """
    Retrieve all meetings from database
    :return: list
    """
    try:
        logger.info("Retrieve all meetings")
        meetings = []
        async for meeting in meeting_collection.find():
            meetings.append(meeting_helper(meeting))
        return meetings
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_meeting_by_pipeline(pipeline: list) -> list:
    """
    Retrieve all meetings from database by pipe
    :param pipe: list
    :return: list
    """
    try:
        pipeline_results = await meeting_collection.aggregate(pipeline).to_list(length=None)
        return [meeting_helper(meeting) for meeting in pipeline_results]
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_meeting_by_id(id: str) -> dict:
    """
    Retrieve a meeting by meeting id
    :param id: str
    :return: dict
    """
    try:
        meeting = await meeting_collection.find_one({"_id": ObjectId(id)})
        if meeting:
            return meeting_helper(meeting)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def update_meeting(id: str, meeting_data: dict) -> dict:
    """
    Update a meeting with a matching ID
    :param id: str
    :param meeting_data: dict
    :return: dict
    """
    try:
        meeting = await meeting_collection.find_one({"_id": ObjectId(id)})
        if not meeting:
            raise Exception("Meeting not found")
        
        updated_meeting = await meeting_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": meeting_data}
        )
        if not updated_meeting:
            raise Exception("Update meeting failed")
        if updated_meeting:
            updated_meeting_data = await meeting_collection.find_one({"_id": ObjectId(id)})
            return meeting_helper(updated_meeting_data)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_meeting(id: str) -> bool:
    """
    Delete a meeting from database by ID. 

    But check if the meeting is in the past dont allow to delete
    :param id: str
    :return: bool
    """
    try:
        meeting = await meeting_collection.find_one({"_id": ObjectId(id)})
        if not meeting:
            raise Exception("Meeting not found")
        if is_past(meeting["date"]):
            raise Exception("Cannot delete meeting in the past")
        deleted_info = await meeting_collection.delete_one({"_id": ObjectId(id)})
        if deleted_info.deleted_count == 1:
            return True
        raise Exception("Delete meeting failed")
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e

