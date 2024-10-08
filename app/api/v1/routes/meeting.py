from typing import List
from datetime import datetime, UTC
from app.utils.logger import Logger
from fastapi import (
    APIRouter, Depends, 
    status, HTTPException
)
from app.core.security import is_admin, is_authenticated
from app.api.v1.controllers.meeting import (
    add_meeting, 
    retrieve_meetings,
    retrieve_meeting_by_id,
    update_meeting,
    delete_meeting
)
from app.schemas.meeting import (
    MeetingSchema, 
    MeetingSchemaDB,
    UpdateMeetingSchema,
    UpdateMeetingSchemaDB
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

@router.get("",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all meetings")
async def get_meetings():
    meetings = await retrieve_meetings()
    if isinstance(meetings, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve meetings failed"
        )
    return ListResponseModel(
        data=meetings,
        message="Meetings retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.get("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve a meeting by meeting id")
async def get_meeting_by_id(id: str):
    meeting = await retrieve_meeting_by_id(id)
    if isinstance(meeting, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve meeting failed"
        )
    return DictResponseModel(
        data=meeting,
        message="Meeting retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a meeting by meeting id")
async def update_meeting_data(id: str, 
                         meeting_data: UpdateMeetingSchema,
                         creator_id: str = Depends(is_authenticated)):
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
            detail="Update meeting failed"
        )
    return DictResponseModel(
        data=updated_meeting,
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
            detail="Delete meeting failed"
        )
    return DictResponseModel(
        data=deleted_meeting,
        message="Meeting deleted successfully",
        code=status.HTTP_200_OK
    )
