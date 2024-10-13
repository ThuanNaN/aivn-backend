from typing import List
from datetime import datetime, UTC
from app.utils.logger import Logger
from fastapi import (
    APIRouter, Depends, Query,
    status, HTTPException
)
from app.utils.time import (
    local_to_utc,
    utc_to_local_default,
    local_to_utc_default
)
from app.core.security import is_admin, is_authenticated
from app.api.v1.controllers.meeting import (
    meeting_helper,
    add_meeting,
    retrieve_meeting_by_pipeline,
    retrieve_meeting_by_id,
    retrieve_upcoming_meeting,
    update_meeting,
    delete_meeting
)
from app.api.v1.controllers.document import (
    document_helper,
    retrieve_document_by_meeting_id,
    upsert_document_by_meeting_id,
)
from app.api.v1.controllers.attendee import (
    attendee_helper,
    add_attendees,
    retrieve_attendees_by_meeting_id,
    delete_attendees_by_emails
)
from app.api.v1.controllers.user import retrieve_user
from app.schemas.meeting import (
    MeetingSchema,
    MeetingSchemaDB,
    UpdateMeetingSchema,
    UpdateMeetingSchemaDB
)
from app.schemas.document import (
    DocumentSchemaDB
)
from app.schemas.response import (
    DictResponseModel,
    ListResponseModel
)


router = APIRouter()
logger = Logger("routes/meeting", log_file="meeting.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new meeting")
async def create_meeting(meeting_data: MeetingSchema,
                         creator_id: str = Depends(is_authenticated)):
    meeting_db = MeetingSchemaDB(
        title=meeting_data.title,
        description=meeting_data.description,
        lecturer=meeting_data.lecturer,
        date=datetime.fromisoformat(meeting_data.date),
        start_time=datetime.fromisoformat(meeting_data.start_time),
        end_time=datetime.fromisoformat(meeting_data.end_time),
        creator_id=creator_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    new_meeting = await add_meeting(meeting_db.model_dump())
    if isinstance(new_meeting, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add meeting failed"
        )
    return DictResponseModel(
        data=new_meeting,
        message="Meeting added successfully",
        code=status.HTTP_201_CREATED
    )


@router.post("/{id}/attendees",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add attendees to a meeting")
async def add_attendees_to_meeting(id: str,
                                   attendee_ids: List[str] | None = None,
                                   attendee_emails: List[str] | None = None
                                   ):
    new_attendees = await add_attendees(id, attendee_ids, attendee_emails)
    if isinstance(new_attendees, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add attendees failed"
        )
    return ListResponseModel(
        data=new_attendees,
        message="Attendees added successfully",
        code=status.HTTP_201_CREATED
    )


@router.get("/meetings",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all meetings")
async def get_meetings(
    time_from: str = Query(None, description="Meeting time from"),
    time_to: str = Query(None, description="Meeting time to"),
    clerk_user_id: str = Depends(is_authenticated)
):
    current_user = await retrieve_user(clerk_user_id)
    if time_from is None or time_to is None:
        now_hcm = utc_to_local_default(datetime.now(UTC))

        time_from = local_to_utc_default(
            now_hcm.replace(hour=0, minute=0, second=0, microsecond=0))
        time_to = local_to_utc_default(
            now_hcm.replace(hour=23, minute=59, second=59, microsecond=999999))
    else:
        time_from = local_to_utc(time_from)
        time_to = local_to_utc(time_to)

    pipeline = [
        {
            '$lookup': {
                'from': 'documents', 
                'localField': '_id', 
                'foreignField': 'meeting_id', 
                'as': 'documents'
            }
        }, 
        {
            '$lookup': {
                'from': 'attendees', 
                'localField': '_id', 
                'foreignField': 'meeting_id', 
                'as': 'attendees'
            }
        },
        {
            "$match": {
                "date": {
                    "$gte": time_from,
                    "$lte": time_to
                },
            }
        }
    ]
    pipeline_results = await retrieve_meeting_by_pipeline(pipeline)
    if isinstance(pipeline_results, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve meetings failed"
        )

    return_data = []
    for result in pipeline_results:
        documents = [document_helper(document)
                     for document in result["documents"]]
        
        return_attendee = None
        for attendee in result["attendees"]:
            if attendee["attend_id"] == current_user["attend_id"]:
                return_attendee = attendee_helper(attendee)
                break

        return_data.append({
            **meeting_helper(result),
            "documents": documents,
            "attendee": return_attendee
        })

    return ListResponseModel(
        data=return_data,
        message="Meetings retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.get("/upcoming",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve upcoming meetings")
async def get_upcoming_meetings():
    upcoming = await retrieve_upcoming_meeting()
    if isinstance(upcoming, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve upcoming meetings failed"
        )
    return DictResponseModel(
        data=upcoming,
        message="Upcoming meetings retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a meeting by meeting id")
async def get_meeting_by_id(id: str):
    meeting_data = await retrieve_meeting_by_id(id)
    if isinstance(meeting_data, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(meeting_data)
        )
    documents = await retrieve_document_by_meeting_id(id)
    if isinstance(documents, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(documents)
        )
    meeting_data["documents"] = documents

    return DictResponseModel(
        data=meeting_data,
        message="Meeting retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.get("/{id}/attendees",
            dependencies=[Depends(is_admin)],
            description="Retrieve attendees by meeting id")
async def get_attendees_by_meeting_id(id: str):
    users = await retrieve_attendees_by_meeting_id(id)
    if isinstance(users, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve attendees failed"
        )
    return ListResponseModel(
        data=users,
        message="Attendees retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a meeting by meeting id")
async def update_meeting_data(id: str,
                              meeting_data: UpdateMeetingSchema,
                              creator_id: str = Depends(is_authenticated)):
    # Update meeting
    meeting_db = UpdateMeetingSchemaDB(
        title=meeting_data.title,
        description=meeting_data.description,
        lecturer=meeting_data.lecturer,
        date=datetime.fromisoformat(meeting_data.date),
        start_time=datetime.fromisoformat(meeting_data.start_time),
        end_time=datetime.fromisoformat(meeting_data.end_time),
        creator_id=creator_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    updated_meeting = await update_meeting(id, meeting_db.model_dump())
    if isinstance(updated_meeting, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(updated_meeting)
        )

    # Upsert documents
    upsert_document_db = [
        DocumentSchemaDB(
            file_name=document["file_name"],
            meeting_id=document["meeting_id"],
            mask_url=document["mask_url"],
            creator_id=creator_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        ).model_dump()
        for document in meeting_data.document_data
    ]
    upserted_documents = await upsert_document_by_meeting_id(
        id,
        upsert_document_db,
    )
    if isinstance(upserted_documents, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(upserted_documents)
        )

    new_documents = await retrieve_document_by_meeting_id(id)
    if isinstance(new_documents, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve documents failed"
        )
    return_data = {
        **updated_meeting,
        "documents": new_documents
    }

    return DictResponseModel(
        data=return_data,
        message="Meeting updated successfully",
        code=status.HTTP_200_OK
    )


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a meeting by meeting id")
async def delete_meeting_data(id: str):
    deleted_meeting = await delete_meeting(id)
    if isinstance(deleted_meeting, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(deleted_meeting)
        )
    return ListResponseModel(
        data=[],
        message="Meeting deleted successfully",
        code=status.HTTP_200_OK
    )


@router.delete("/{id}/attendees",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete attendees by emails")
async def delete_attendees_data_by_emails(id: str, emails: List[str]):
    deleted_attendees = await delete_attendees_by_emails(id, emails)
    if isinstance(deleted_attendees, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(deleted_attendees)
        )
    return ListResponseModel(
        data=[],
        message="Attendees deleted successfully",
        code=status.HTTP_200_OK
    )
