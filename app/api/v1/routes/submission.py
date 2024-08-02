from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from bson.objectid import ObjectId
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.submission import (
    retrieve_search_filter_pagination,
    retrieve_submission_by_id,
    retrieve_submission_by_id_user_retake,
    delete_submission,
)
from app.api.v1.controllers.timer import (
    delete_timer_by_user_id,
    delete_timer_by_exam_retake_user_id
)
from app.api.v1.controllers.retake import (
    retrieve_retake_by_user_exam_id,
    delete_retake_by_ids
)
from app.core.security import is_admin, is_authenticated
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/submission", log_file="submission.log")


@router.get("/submissions",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Get all submissions")
async def get_submissions(
    search: Optional[str] = Query(
        None, description="Search by user, email, contest or exam title"),
    contest_id: Optional[str] = Query(
        None, description="Filter by contest id"),
    exam_id: Optional[str] = Query(None, description="Filter by exam id"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"user_info.email": {"$regex": search, "$options": "i"}},
            {"user_info.username": {"$regex": search, "$options": "i"}},
            {"exam_info.title": {"$regex": search, "$options": "i"}},
            {"contest_info.title": {"$regex": search, "$options": "i"}}
        ]

    if user_id is not None:
        match_stage["$match"]["clerk_user_id"] = user_id

    if exam_id is not None:
        match_stage["$match"]["exam_id"] = ObjectId(exam_id)

    if contest_id is not None:
        match_stage["$match"]["exam_info.contest_id"] = ObjectId(contest_id)

    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "clerk_user_id",
                "foreignField": "clerk_user_id",
                "as": "user_info"
            }
        },
        {
            "$unwind": "$user_info"
        },
        {
            "$lookup": {
                "from": "exams",
                "localField": "exam_id",
                "foreignField": "_id",
                "as": "exam_info"
            }
        },
        {
            "$unwind": "$exam_info"
        },
        {
            "$lookup": {
                "from": "contests",
                "localField": "exam_info.contest_id",
                "foreignField": "_id",
                "as": "contest_info"
            }
        },
        {
            "$unwind": "$contest_info"
        },
        match_stage,
        {
            "$facet": {
                "submissions": [
                    {
                        "$skip": (page - 1) * per_page
                    },
                    {
                        "$limit": per_page
                    }
                ],
                "total": [
                    {
                        "$count": "count"
                    }
                ]
            }
        },
    ]

    submissions = await retrieve_search_filter_pagination(pipeline, page, per_page)
    if isinstance(submissions, Exception):
        return ErrorResponseModel(error=str(submissions),
                                  message="An error occurred while retrieving submissions.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=submissions,
                             message="Submissions retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/exam/{exam_id}/my-submission", description="Retrieve a submission by user ID")
async def get_submission_by_user(exam_id: str,
                                 retake_id: Optional[str] = None,
                                 clerk_user_id: str = Depends(is_authenticated)):
    submission = await retrieve_submission_by_id_user_retake(exam_id, 
                                                             retake_id,
                                                             clerk_user_id)
    if isinstance(submission, Exception):
        return ErrorResponseModel(error=str(submission),
                                  message="An error occurred while retrieving submission.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not submission:
        return ErrorResponseModel(error="Submission not found.",
                                  message="No submission found.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=submission,
                             message="Your submission retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}", description="Retrieve a submission with a matching ID")
async def get_submission(id: str):
    submission = await retrieve_submission_by_id(id)
    if isinstance(submission, Exception):
        return ErrorResponseModel(error=str(submission),
                                  message="An error occurred while retrieving submission.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=submission,
                             message="Submission retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               description="Delete a submission with a matching ID")
async def delete_submission_data(id: str):
    submission_info = await retrieve_submission_by_id(id)
    if isinstance(submission_info, Exception):
        return ErrorResponseModel(error=str(submission_info),
                                  message="An error occurred while retrieving submission.",
                                  code=status.HTTP_404_NOT_FOUND)
    clerk_user_id = submission_info["clerk_user_id"]

    # Delete retake if exists
    retakes = await retrieve_retake_by_user_exam_id(clerk_user_id=clerk_user_id, 
                                                    exam_id=submission_info["exam_id"])
    if isinstance(retakes, Exception):
        return ErrorResponseModel(error=str(retakes),
                                  message="An error occurred while retrieving retakes.",
                                  code=status.HTTP_404_NOT_FOUND)
    if retakes:
        retake_ids = [ObjectId(retake["id"]) for retake in retakes]
        deleted_retakes = await delete_retake_by_ids(retake_ids)
        if isinstance(deleted_retakes, Exception):
            return ErrorResponseModel(error=str(deleted_retakes),
                                      message="An error occurred while deleting retakes.",
                                      code=status.HTTP_404_NOT_FOUND)
        if not deleted_retakes:
            return ErrorResponseModel(error="An error occurred while deleting retakes.",
                                      message="Retakes were not deleted.",
                                      code=status.HTTP_404_NOT_FOUND)
    # Delete timer
    deleted_timer = await delete_timer_by_exam_retake_user_id(exam_id=submission_info["exam_id"],
                                                              clerk_user_id=clerk_user_id,
                                                              retake_id=submission_info["retake_id"])
    if isinstance(deleted_timer, Exception):
        return ErrorResponseModel(error=str(deleted_timer),
                                  message="An error occurred while deleting timer.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not deleted_timer:
        return ErrorResponseModel(error="An error occurred while deleting timer.",
                                  message="Timer was not deleted.",
                                  code=status.HTTP_404_NOT_FOUND)
    # Delete submission
    deleted_submission = await delete_submission(id)
    if isinstance(deleted_submission, Exception):
        return ErrorResponseModel(error=str(deleted_submission),
                                  message="An error occurred while deleting submission.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not deleted_submission:
        return ErrorResponseModel(error="An error occurred while deleting submission.",
                                  message="Submission was not deleted.",
                                  code=status.HTTP_404_NOT_FOUND)

    return ListResponseModel(data=[],
                             message="Submission deleted successfully.",
                             code=status.HTTP_200_OK)
