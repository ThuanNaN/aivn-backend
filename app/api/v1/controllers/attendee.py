import traceback
from datetime import datetime, UTC
from app.utils.time import utc_to_local
from app.core.database import mongo_client, mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId
from app.schemas.attendee import AttendeeSchemaDB
from app.api.v1.controllers.user import user_helper

logger = Logger("controllers/attendee", log_file="attendee.log")
try:
    attendee_collection = mongo_db["attendees"]
    user_collection = mongo_db["users"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper
def attendee_helper(attendee: dict) -> dict:
    return {
        "id": str(attendee["_id"]),
        "attend_id": attendee["attend_id"],
        "meeting_id": str(attendee["meeting_id"]),
        "created_at": utc_to_local(attendee["created_at"]),
        "updated_at": utc_to_local(attendee["updated_at"])
    }


async def add_attendees(meeting_id, attendee_ids, attendee_emails) -> list[str]:
    """
    Add a list of attendees to database

    :param meeting_id: str
    :param attendee_ids: list
    :param attendee_emails: list
    
    :return: dict
    """
    try:
        if attendee_ids is None:
            attendee_ids = []
        attendee_ids = [attendee_id.zfill(4) for attendee_id in attendee_ids] 
        if attendee_emails is not None:
            user_info = await user_collection.find(
                {"email": {"$in": attendee_emails}},
                {"attend_id": 1}
            ).to_list(length=None)
            attendee_ids.extend([user["attend_id"] for user in user_info])

        current_attendees = await retrieve_attendees_by_meeting_id(meeting_id)
        current_attendees = [attendee["attend_id"] for attendee in current_attendees]
        new_attendees = [attendee_id for attendee_id in attendee_ids if attendee_id not in current_attendees]
       
        attendee_data = []
        for attendee_ids in new_attendees:
            attendee_db = AttendeeSchemaDB(
                meeting_id=meeting_id,
                attend_id=attendee_ids,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            ).model_dump()
            attendee_db["meeting_id"] = ObjectId(attendee_db["meeting_id"])
            attendee_data.append(attendee_db)

        if len(attendee_data) == 0:
            return []
        new_attendees = await attendee_collection.insert_many(attendee_data)
        return [str(attendee) for attendee in new_attendees.inserted_ids]
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_attendees_by_meeting_id(meeting_id: str) -> list[dict]:
    """
    Retrieve all attendees by meeting_id

    :param meeting_id: str

    :return: list
    """
    try:
        pipeline = [
            {
                "$match": {
                    "meeting_id": ObjectId(meeting_id)
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "attend_id",
                    "foreignField": "attend_id",
                    "as": "user_info"
                }
            },
            {
                "$unwind": "$user_info"
            },
            {
                "$replaceRoot": {
                    "newRoot": "$user_info"
                }
            }
        ]
        attendees = await attendee_collection.aggregate(pipeline).to_list(length=None)
        return [user_helper(attendee) for attendee in attendees]
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_attendees_by_emails(meeting_id: str, emails: list[str]) -> bool:
    """
    Delete attendees by emails

    :param meeting_id: str

    :param emails: list

    :return: bool
    """
    async with await mongo_client.start_session() as session:
        try:
            async with session.start_transaction():
                user_info = await user_collection.find(
                    {"email": {"$in": emails}},
                    {"attend_id": 1}
                ).to_list(length=None)
                attendee_ids = [user["attend_id"] for user in user_info]

                if len(emails) != len(attendee_ids):
                    raise Exception("Some emails not found")

                result = await attendee_collection.delete_many(
                    {
                        "meeting_id": ObjectId(meeting_id),
                        "attend_id": {"$in": attendee_ids}
                    }
                )
                if result.deleted_count != len(attendee_ids):
                    raise Exception("Delete attendees failed")
        except Exception as e:
            logger.error(f"{traceback.format_exc()}")
            return e
        else: 
            logger.info(f"Deleted attendees by emails: {emails}")
            return True