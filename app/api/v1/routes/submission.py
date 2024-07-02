from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.submission import (
    SubmissionSchema,
    ResponseModel,
    ErrorResponseModel
)
from app.schemas.setting import (
    SettingSchema,
    ResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.submission import (
    run_testcases,
    add_submission,
    retrieve_submissions,
    retrieve_all_search_pagination,
    retrieve_submission,
    retrieve_submission_by_user,
    delete_submission,

    add_time_limit,
    retrieve_time_limit,
    retrieve_time_limits,
    update_time_limit
)
from app.api.v1.controllers.do_exam import (
    delete_timer_by_user_id
)
from app.core.security import is_admin, is_authenticated
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/submission", log_file="submission.log")


@router.post("/submit",
             description="Submit code to a test")
async def submit_code(submission_data: SubmissionSchema):
    submission_dict = submission_data.model_dump()

    submitted_problems = submission_dict["problems"]

    problem_results = []
    total_score = 0

    for submitted in submitted_problems:
        # problem ==> {
        #   "problem_id":
        #   "submitted_code":
        #   "submitted_choice":
        # }

        problem_id = submitted["problem_id"]
        # def test_py_funct(): return 1
        submitted_code = submitted["submitted_code"]
        submitted_choice = submitted["submitted_choice"]  # id_1,id_2

        problem_info = await retrieve_problem(problem_id)
        # ==>  return {
        #     "id":
        #     "title":
        #     "description":
        #     "index":
        #     "code_template":
        #     "admin_template":
        #     "public_testcases":
        #     "private_testcases":
        #     "choices":
        #     "created_at":
        #     "updated_at":
        # }

        if not problem_info:
            logger.error(f'Problem with ID {problem_id} not found.')
            return ErrorResponseModel(error="An error occurred when retrieving problem.",
                                      message="Problem not found.",
                                      code=status.HTTP_404_NOT_FOUND)

        public_results, private_results = None, None

        if submitted_code is not None:
            admin_template = problem_info.get("admin_template", "")
            public_testcases = problem_info.get("public_testcases", [])
            private_testcases = problem_info.get("private_testcases", [])

            public_results, is_pass_public = await run_testcases(
                admin_template,
                submitted_code,
                public_testcases
            )

            private_results, is_pass_private = await run_testcases(
                admin_template,
                submitted_code,
                private_testcases
            )

            is_pass_problem = is_pass_public and is_pass_private
            total_score += int(is_pass_problem)

        if submitted_choice is not None:
            choice_answers = submitted_choice.split(",")  # -> ["id_1", "id_2"]
            true_answers_id = [str(choice["choice_id"])
                               for choice in problem_info["choices"]
                               if choice["is_correct"]]

            if len(choice_answers) != len(true_answers_id):
                is_pass_problem = False
            else:
                is_pass_problem = sorted(
                    choice_answers) == sorted(true_answers_id)
            total_score += int(is_pass_problem)

        problem_results.append(
            {
                "problem_id": problem_id,
                "submitted_code": submitted_code,
                "submitted_choice": submitted_choice,
                "title": problem_info["title"],
                "description": problem_info["description"],
                "public_testcases_results": public_results,
                "private_testcases_results": private_results,
                "choice_results": problem_info["choices"],
                "is_pass_problem": is_pass_problem
            }
        )

    submission_dict["problems"] = problem_results
    try:
        _ = await add_submission(submission_dict)
        return ResponseModel(
            data={
                "total_score": total_score,
                "total_problems": len(submitted_problems)
            },
            message="Submission added successfully.",
            code=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error when add submission: {e}")
        return ErrorResponseModel(
            error="An error occurred.",
            message="Unable to add submission.",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# @router.get("/submissions",
#             dependencies=[Depends(is_admin)],
#             tags=["Admin"],
#             description="Get all submissions")
# async def get_submissions():
#     submissions = await retrieve_submissions()
#     if submissions:
#         return ResponseModel(data=submissions,
#                              message="Submissions retrieved successfully.",
#                              code=status.HTTP_200_OK)
#     return ResponseModel(data=[],
#                          message="No submissions exist.",
#                          code=status.HTTP_404_NOT_FOUND)


@router.get("/submissions",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Get all submissions")
async def get_submissions(
    search: Optional[str] = Query(None, description="Search by user email"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"user_info.email": {"$regex": search, "$options": "i"}},  # Case-insensitive regex search on email
            {"user_info.username": {"$regex": search, "$options": "i"}}  # Case-insensitive regex search on username
        ]
    pipeline = [
        {
            "$lookup": {
                "from": "users",  # The collection to join
                "localField": "user_id",  # Field from the submissions collection
                "foreignField": "clerk_user_id",  # Field from the users collection
                "as": "user_info"  # The name of the new array field to add to the input documents
            }
        },
        {
            "$unwind": "$user_info"  # Deconstructs the array field from the previous stage
        },
        match_stage,
        {
            "$project": {
                "user_id": 1,
                "username": "$user_info.username",
                "email": "$user_info.email",
                "avatar": "$user_info.avatar",
                "problems": 1,
                "created_at": 1
            }
        },
        {
            "$skip": (page - 1) * per_page
        },
        {
            "$limit": per_page
        }
    ]

    submissions = await retrieve_all_search_pagination(pipeline, match_stage, page, per_page)
    if submissions:
        return ResponseModel(data=submissions,
                             message="Submissions retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ResponseModel(data=[],
                         message="No submissions exist.",
                         code=status.HTTP_404_NOT_FOUND)


@router.get("/my-submission", description="Retrieve a submission by user ID")
async def get_submission_by_user(user_id: str = Depends(is_authenticated)):
    submission = await retrieve_submission_by_user(user_id)
    if submission:
        return ResponseModel(data=submission,
                             message="Your submission retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Your submission was not retrieved.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}", description="Retrieve a submission with a matching ID")
async def get_submission(id: str):
    submission = await retrieve_submission(id)
    if submission:
        return ResponseModel(data=submission,
                             message="Submission retrieved successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Submission was not retrieved.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               description="Delete a submission with a matching ID")
async def delete_submission_data(id: str):
    submission_info = await retrieve_submission(id)
    user_id = submission_info["user_id"]
    deleted_timer = await delete_timer_by_user_id(user_id)
    deleted_submission = await delete_submission(id)
    if deleted_submission and deleted_timer:
        return ResponseModel(data=[],
                             message="Submission deleted successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Submission was not deleted.",
                              code=status.HTTP_404_NOT_FOUND)


# >>> Setting Exam
@router.post("/time/time-limit", description="Set time limit for submission")
async def set_time_limit(setting_data: SettingSchema):
    setting = setting_data.model_dump()

    time_limits = await retrieve_time_limits()
    if len(time_limits) > 1:
        return ErrorResponseModel(error="An error occurred.",
                                  message="Time limit more than 1.",
                                  code=status.HTTP_400_BAD_REQUEST)
    if time_limits:
        time_limit_id = time_limits[0]["id"]
        await update_time_limit(time_limit_id, setting)
    else:
        await add_time_limit(setting)

    new_setting = await retrieve_time_limit(time_limit_id)
    if new_setting:
        return ResponseModel(data=new_setting,
                             message="New time limit set successfully.",
                             code=status.HTTP_200_OK)
    return ErrorResponseModel(error="An error occurred.",
                              message="Time limit was not set.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/time/time-limit", description="Get time limit for submission")
async def get_time_limit():
    setting = await retrieve_time_limits()
    if len(setting) == 1:
        return ResponseModel(data=setting[0],
                             message="Time limit retrieved successfully.",
                             code=status.HTTP_200_OK)
    if not setting:
        return ErrorResponseModel(error="An error occurred.",
                                  message="Time limit not found.",
                                  code=status.HTTP_404_NOT_FOUND)
