from pprint import pprint
from fastapi import APIRouter
from app.schemas.submission import (
    SubmissionSchema,
    ResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.submission import (
    run_testcases,
    add_submission,
    retrieve_submissions,
    retrieve_submission
)
from app.utils.logger import Logger


router = APIRouter()
logger = Logger("routes/submission", log_file="submission.log")


@router.post("/submit", description="Submit code to a test")
async def submit_code(submission_data: SubmissionSchema):
    submission_dict = submission_data.model_dump()
    problems_submited = submission_dict["problems"]

    problem_results = []
    total_score = 0

    for problem in problems_submited:
        problem_id = problem["problem_id"]
        submited_code = problem["submited_code"]

        problem_info = await retrieve_problem(problem_id)
        if not problem_info:
            logger.error(f'Problem with ID {problem_id} not found.')
            return ErrorResponseModel(error="An error occurred.",
                                      message="Problem not found.",
                                      code=404)

        public_testcases = problem_info.get("public_testcases", [])
        private_testcases = problem_info.get("private_testcases", [])

        public_results, is_pass_public = run_testcases(
            submited_code, public_testcases)
        private_results, is_pass_private = run_testcases(
            submited_code, private_testcases)

        is_pass_problem = is_pass_public and is_pass_private
        total_score += int(is_pass_problem)

        problem_results.append(
            {
                "problem_id": problem_id,
                "title": problem_info["title"],
                "description": problem_info["description"],
                "submited_code": submited_code,
                "public_testcases_results": public_results,
                "private_testcases_results": private_results,
                "is_pass_problem": is_pass_problem
            }
        )

    submission_dict["problems"] = problem_results
    try:
        _ = await add_submission(submission_dict)
        return ResponseModel(
            data={
                "total_score": total_score,
                "total_problems": len(problems_submited)
            },
            message="Submission added successfully.",
            code=200)

    except Exception as e:
        logger.error(f"Error when add submission: {e}")
        return ErrorResponseModel(
            error="An error occurred.",
            message="Unable to add submission.",
            code=500
        )


@router.get("/submissions", description="Get all submissions")
async def get_submissions():
    submissions = await retrieve_submissions()
    if submissions:
        return ResponseModel(data=submissions,
                             message="Submissions retrieved successfully.",
                             code=200)
    return ResponseModel(data=[],
                         message="No submissions exist.",
                         code=404)

@router.get("/{id}", description="Retrieve a submission with a matching ID")
async def get_submission(id: str):
    submission = await retrieve_submission(id)
    if submission:
        return ResponseModel(data=submission,
                             message="Submission retrieved successfully.",
                             code=200)
    return ErrorResponseModel(error="An error occurred.",
                              message="Submission was not retrieved.",
                              code=404)
