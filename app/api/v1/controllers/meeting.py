import traceback
from datetime import datetime, UTC
from pymongo.errors import ConnectionFailure, OperationFailure
from app.utils.time import utc_to_local, is_past
from app.core.database import mongo_client, mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/meeting", log_file="meeting.log")
try:
    meeting_collection = mongo_db["meetings"]
    document_collection = mongo_db["documents"]
    attendee_collection = mongo_db["attendees"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
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
        return pipeline_results
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
        raise Exception("Meeting not found")
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
        if updated_meeting.modified_count > 0:
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
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
    
    # Transaction to delete meeting and documents
    async with await mongo_client.start_session() as session:
        try:
            async with session.start_transaction():
                del_meeting = await meeting_collection.delete_one(
                    {"_id": ObjectId(id)},
                    session=session)
                logger.info(f"Delete meeting with ID: {id}")
                del_documents = await document_collection.delete_many(
                    {"meeting_id": ObjectId(id)},
                    session=session)
                logger.info(f"Delete documents: {del_documents.deleted_count}")
                del_attendees = await attendee_collection.delete_many(
                    {"meeting_id": ObjectId(id)},
                    session=session)
                logger.info(f"Delete attendees: {del_attendees.deleted_count}")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"{traceback.format_exc()}")
            return e
        else:
            if del_meeting.deleted_count == 1:
                return True
            raise Exception("Delete meeting failed")
        

async def retrieve_upcoming_meeting() -> dict:
    """
    Get all an upcoming meeting

    :return: dict
    """
    try:
        current_utc_time = datetime.now(UTC)
        pipeline = [
            {"$match": {"date": {"$gte": current_utc_time}}},
            {"$sort": {"date": 1}},
            {"$limit": 1}
        ]
        upcoming_meeting = await meeting_collection.aggregate(pipeline).to_list(length=None)
        if upcoming_meeting:
            return meeting_helper(upcoming_meeting[0])
        raise Exception("Upcoming meeting not found")
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e