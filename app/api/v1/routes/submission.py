from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.submission import (
    Submission
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.submission import (
    retrieve_submissions,
    retrieve_all_search_pagination,
    retrieve_submission_by_id,
    retrieve_submission_by_exam_user_id,
    delete_submission,
)
from app.api.v1.controllers.timer import (
    delete_timer_by_user_id
)
from app.core.security import is_admin, is_authenticated
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/submission", log_file="submission.log")


# @router.get("/submissions",
#             dependencies=[Depends(is_admin)],
#             tags=["Admin"],
#             description="Get all submissions")
# async def get_submissions(
#     search: Optional[str] = Query(None, description="Search by user or email"),
#     # contest: Optional[str] = Query(None, description="Filter by contest name"),
#     exam: Optional[str] = Query(None, description="Filter by exam name"),
#     page: int = Query(1, ge=1),
#     per_page: int = Query(10, ge=1, le=100)
# ):
#     match_stage = {"$match": {}}
#     if search:
#         match_stage["$match"]["$or"] = [
#             {"user_info.email": {"$regex": search, "$options": "i"}},
#             {"user_info.username": {"$regex": search, "$options": "i"}}
#         ]
#     pipeline = [
#         {
#             "$lookup": {
#                 "from": "users",
#                 "localField": "clerk_user_id",
#                 "foreignField": "clerk_user_id",
#                 "as": "user_info"
#             }
#         },
#         {
#             "$unwind": "$user_info"
#         },
#         {
#             "$lookup": {
#                 "from": "exams",
#                 "localField": "exam_id",
#                 "foreignField": "_id",
#                 "as": "exam_info"
#             }
#         },
#         {
#             "$unwind": "$exam_info"
#         },
#         {
#             "$match": {
#                 "exam_info.title": {"$regex": exam, "$options": "i"} if exam else {"$exists": True}
#             }
#         },
#         match_stage,
#         {
#             "$project": {
#                 "clerk_user_id": "$user_info.clerk_user_id",
#                 "username": "$user_info.username",
#                 "email": "$user_info.email",
#                 "avatar": "$user_info.avatar",
#                 "exam_id": "$exam_info._id",
#                 "submitted_problems": 1,
#                 "created_at": 1
#             }
#         },
#         {
#             "$skip": (page - 1) * per_page
#         },
#         {
#             "$limit": per_page
#         }
#     ]

#     submissions = await retrieve_all_search_pagination(pipeline, match_stage, page, per_page)
#     if submissions:
#         return DictResponseModel(data=submissions,
#                              message="Submissions retrieved successfully.",
#                              code=status.HTTP_200_OK)
#     return ListResponseModel(data=[],
#                          message="No submissions exist.",
#                          code=status.HTTP_404_NOT_FOUND)


@router.get("/exam/{exam_id}/my-submission", description="Retrieve a submission by user ID")
async def get_submission_by_user(exam_id: str,
                                 clerk_user_id: str = Depends(is_authenticated)):
    submission = await retrieve_submission_by_exam_user_id(exam_id, clerk_user_id)
    if submission:
        return DictResponseModel(data=submission,
                                 message="Your submission retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Your submission was not retrieved.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}", description="Retrieve a submission with a matching ID")
async def get_submission(id: str):
    submission = await retrieve_submission_by_id(id)
    if submission:
        return DictResponseModel(data=submission,
                                 message="Submission retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Submission was not retrieved.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               description="Delete a submission with a matching ID")
async def delete_submission_data(id: str):
    submission_info = await retrieve_submission_by_id(id)
    clerk_user_id = submission_info["clerk_user_id"]
    deleted_timer = await delete_timer_by_user_id(clerk_user_id)
    deleted_submission = await delete_submission(id)
    if deleted_submission and deleted_timer:
        return ListResponseModel(data=[],
                                 message="Submission deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Submission was not deleted.",
                              code=status.HTTP_404_NOT_FOUND)
