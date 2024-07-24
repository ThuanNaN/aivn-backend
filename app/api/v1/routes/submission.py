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
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.submission import (
    add_submission,
    retrieve_submissions,
    retrieve_all_search_pagination,
    retrieve_submission,
    retrieve_submission_by_user,
    delete_submission,
    update_time_limit
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
#     search: Optional[str] = Query(None, description="Search by user email"),
#     page: int = Query(1, ge=1),
#     per_page: int = Query(10, ge=1, le=100)
# ):
#     match_stage = {"$match": {}}
#     if search:
#         match_stage["$match"]["$or"] = [
#             {"user_info.email": {"$regex": search, "$options": "i"}},  # Case-insensitive regex search on email
#             {"user_info.username": {"$regex": search, "$options": "i"}}  # Case-insensitive regex search on username
#         ]
#     pipeline = [
#         {
#             "$lookup": {
#                 "from": "users",  # The collection to join
#                 "localField": "user_id",  # Field from the submissions collection
#                 "foreignField": "clerk_user_id",  # Field from the users collection
#                 "as": "user_info"  # The name of the new array field to add to the input documents
#             }
#         },
#         {
#             "$unwind": "$user_info"  # Deconstructs the array field from the previous stage
#         },
#         match_stage,
#         {
#             "$project": {
#                 "user_id": 1,
#                 "username": "$user_info.username",
#                 "email": "$user_info.email",
#                 "avatar": "$user_info.avatar",
#                 "problems": 1,
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


# @router.get("/my-submission", description="Retrieve a submission by user ID")
# async def get_submission_by_user(user_id: str = Depends(is_authenticated)):
#     submission = await retrieve_submission_by_user(user_id)
#     if submission:
#         return DictResponseModel(data=submission,
#                              message="Your submission retrieved successfully.",
#                              code=status.HTTP_200_OK)
#     return ErrorResponseModel(error="An error occurred.",
#                               message="Your submission was not retrieved.",
#                               code=status.HTTP_404_NOT_FOUND)


# @router.get("/{id}", description="Retrieve a submission with a matching ID")
# async def get_submission(id: str):
#     submission = await retrieve_submission(id)
#     if submission:
#         return DictResponseModel(data=submission,
#                              message="Submission retrieved successfully.",
#                              code=status.HTTP_200_OK)
#     return ErrorResponseModel(error="An error occurred.",
#                               message="Submission was not retrieved.",
#                               code=status.HTTP_404_NOT_FOUND)


# @router.delete("/{id}",
#                dependencies=[Depends(is_admin)],
#                description="Delete a submission with a matching ID")
# async def delete_submission_data(id: str):
#     submission_info = await retrieve_submission(id)
#     user_id = submission_info["user_id"]
#     deleted_timer = await delete_timer_by_user_id(user_id)
#     deleted_submission = await delete_submission(id)
#     if deleted_submission and deleted_timer:
#         return ListResponseModel(data=[],
#                              message="Submission deleted successfully.",
#                              code=status.HTTP_200_OK)
#     return ErrorResponseModel(error="An error occurred.",
#                               message="Submission was not deleted.",
#                               code=status.HTTP_404_NOT_FOUND)

