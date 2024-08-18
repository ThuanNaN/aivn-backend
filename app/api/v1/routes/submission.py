from typing import Optional
import pandas as pd
from io import StringIO
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from bson.objectid import ObjectId
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.exam import exam_helper
from app.api.v1.controllers.contest import contest_helper
from app.api.v1.controllers.user import (
    retrieve_user,
    user_helper
)
from app.api.v1.controllers.problem import (
    retrieve_problem
)
from app.api.v1.controllers.submission import (
    submission_helper,
    retrieve_submission_by_pipeline,
    retrieve_submission_by_id_user_retake,
    delete_submission,
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

    pipeline_results = await retrieve_submission_by_pipeline(pipeline)
    if isinstance(pipeline_results, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving submissions failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not pipeline_results[0]["submissions"]:
        return ErrorResponseModel(error="No submissions found.",
                                  message="No submissions found.",
                                  code=status.HTTP_404_NOT_FOUND)

    total_submissions = pipeline_results[0]["total"][0]["count"]
    submissions = pipeline_results[0]["submissions"]
    if len(submissions) < 1:
        return_data = {
            "submissions_data": [],
            "total_submissions": 0,
            "total_pages": 0,
            "current_page": page,
            "per_page": per_page
        }
    else:
        submissions_data = []
        for submission in submissions:
            submissions_data.append(
                {
                    **submission_helper(submission),
                    "contest_info": contest_helper(submission["contest_info"]),
                    "exam_info": exam_helper(submission["exam_info"]),
                    "user_info": user_helper(submission["user_info"])
                }
            )
        return_data = {
            "submissions_data": submissions_data,
            "total_submissions": total_submissions,
            "total_pages": (total_submissions + per_page - 1) // per_page,
            "current_page": page,
            "per_page": per_page
        }
    return DictResponseModel(data=return_data,
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
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving submission failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not submission:
        return ErrorResponseModel(error="Submission not found.",
                                  message="No submission found.",
                                  code=status.HTTP_404_NOT_FOUND)
    user_info = await retrieve_user(clerk_user_id)
    submission["user"] = user_info
    return DictResponseModel(data=submission,
                             message="Your submission retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}", description="Retrieve a submission with a matching ID")
async def get_submission(id: str):
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
                "as": "exam_info.contest_info"
            }
        },
        {
            "$unwind": "$exam_info.contest_info"
        },
        {
            "$match": {
                "_id": ObjectId(id)
            }
        }
    ]

    pipeline_results = await retrieve_submission_by_pipeline(pipeline)
    if isinstance(pipeline_results, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving submission failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not pipeline_results[0]:
        return ErrorResponseModel(error="Submission not found.",
                                  message="No submission found.",
                                  code=status.HTTP_404_NOT_FOUND)
    
    for problem in pipeline_results[0]["submitted_problems"]:
        problem_info = await retrieve_problem(problem["problem_id"], full_return=True)
        problem["solution_code"] = problem_info["code_solution"]

    exam_info = exam_helper(pipeline_results[0]["exam_info"])
    exam_info["contest_info"] = contest_helper(pipeline_results[0]["exam_info"]["contest_info"])

    return_data = {
        **submission_helper(pipeline_results[0]),
        "user_info": user_helper(pipeline_results[0]["user_info"]),
        "exam_info": exam_info
    }
    return DictResponseModel(data=return_data,
                             message="Submission retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               description="Delete a submission with a matching ID")
async def delete_submission_data(id: str):
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


@router.get("/export/submissions",
            response_class=StreamingResponse,
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Export all submissions to CSV file")
async def export_submissions(
    search: Optional[str] = Query(
        None, description="Search by user, email, contest or exam title"),
    contest_id: Optional[str] = Query(
        None, description="Filter by contest id"),
    exam_id: Optional[str] = Query(None, description="Filter by exam id"),
):

    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"user_info.email": {"$regex": search, "$options": "i"}},
            {"user_info.username": {"$regex": search, "$options": "i"}},
            {"exam_info.title": {"$regex": search, "$options": "i"}},
            {"contest_info.title": {"$regex": search, "$options": "i"}}
        ]

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
                "submissions": [],
                "total": [
                    {
                        "$count": "count"
                    }
                ]
            }
        },
    ]
    pipeline_results = await retrieve_submission_by_pipeline(pipeline)
    if isinstance(pipeline_results, Exception):
        return ErrorResponseModel(error="Export submissions failed.",
                                  message="An error occurred.",
                                  code=status.HTTP_404_NOT_FOUND)
    submissions = pipeline_results[0]["submissions"]
    if not submissions:
        return ErrorResponseModel(error="No submissions found.",
                                  message="No submissions found.",
                                  code=status.HTTP_404_NOT_FOUND)
    outputs = []
    for submission in submissions:
        submitted_problems = submission.pop("submitted_problems")

        return_data = {}
        return_data["id"] = str(submission["_id"])
        return_data["user_id"] = submission["clerk_user_id"]
        return_data["username"] = submission["user_info"]["username"]
        return_data["email"] = submission["user_info"]["email"]
        return_data["username"] = submission["user_info"]["username"]
        return_data["role"] = submission["user_info"]["role"]

        return_data["contest_id"] = str(submission["exam_info"]["contest_id"])
        return_data["contest_title"] = submission["contest_info"]["title"]
        return_data["contest_description"] = submission["contest_info"]["description"]

        return_data["exam_id"] = str(submission["exam_id"])
        return_data["exam_title"] = submission["exam_info"]["title"]
        return_data["exam_description"] = submission["exam_info"]["description"]
        return_data["exam_duration"] = submission["exam_info"]["duration"]
        return_data["retake_exam_id"] = str(submission["retake_id"])

        return_data["total_problems"] = submission["total_problems"]
        return_data["total_passes"] = submission["total_problems"]

        return_data["submit_at"] = str(submission["created_at"])
        outputs.append(return_data)

    df = pd.DataFrame(submissions)
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(output,
                             media_type="text/csv",
                             headers={
                                 "Content-Disposition": "attachment;filename=submissions.csv"}
                             )
