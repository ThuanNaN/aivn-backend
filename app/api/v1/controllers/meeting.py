import traceback
from app.utils import utc_to_local, is_past, MessageException
from fastapi import status
from app.core.database import mongo_client, mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.api.v1.controllers.document import document_helper

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
        "creator_id": str(meeting["creator_id"]),
        "join_link": meeting["join_link"],
        "record": meeting["record"],
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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add meeting", 
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when retrieve meetings",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_meeting_by_pipeline(pipeline: list) -> list:
    """
    Retrieve all meetings from database by pipe
    :param pipe: list
    :return: list
    """
    try:
        pipeline_results = await meeting_collection.aggregate(pipeline).to_list(length=None)
        return pipeline_results
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when retrieve meetings",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_meeting_by_id(id: str) -> dict:
    """
    Retrieve a meeting by meeting id
    :param id: str
    :return: dict
    """
    try:
        meeting = await meeting_collection.find_one({"_id": ObjectId(id)})
        if not meeting:
            raise MessageException("Meeting not found", 
                                status.HTTP_404_NOT_FOUND)
        return meeting_helper(meeting)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when retrieve meeting", 
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            raise MessageException("Meeting not found", 
                                   status.HTTP_404_NOT_FOUND)
        
        updated_meeting = await meeting_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": meeting_data}
        )
        if updated_meeting.modified_count == 0:
            raise MessageException("Update meeting failed", 
                                   status.HTTP_400_BAD_REQUEST)
        updated_meeting_data = await meeting_collection.find_one({"_id": ObjectId(id)})
        return meeting_helper(updated_meeting_data)

    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when update meeting",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            raise MessageException("Meeting not found",
                                   status.HTTP_404_NOT_FOUND)
        
        if is_past(meeting["date"], "utc"):
            raise MessageException("Cannot delete meeting in the past",
                                   status.HTTP_400_BAD_REQUEST)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when delete meeting",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        except:
            logger.error(f"{traceback.format_exc()}")
            return MessageException("An error occurred when delete meeting",
                                    status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            if del_meeting.deleted_count == 0:
                raise MessageException("Delete meeting failed",
                                        status.HTTP_400_BAD_REQUEST)
            return True
        
        

async def retrieve_upcoming_meeting_by_pipeline(pipeline: list) -> dict:
    """
    Get all an upcoming meeting
    :param pipeline: list
    :return: dict
    """
    try:
        upcoming_meeting = await meeting_collection.aggregate(pipeline).to_list(length=None)
        if upcoming_meeting:
            return {
                **meeting_helper(upcoming_meeting[0]),
                "documents": [document_helper(document) for document in upcoming_meeting[0]["documents"]]
            }
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("An error occurred when retrieve upcoming meeting",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return {}
    