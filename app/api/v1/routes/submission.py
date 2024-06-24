from fastapi import APIRouter
from app.schemas.submission import (
    SubmissionSchema,
    ResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.run_code import test_py_funct
from app.api.v1.controllers.submission import (
    add_submission,
    pass_testcases
)
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/submission", log_file="submission.log")


@router.post("/submit", description="Submit code to a test")
async def submit_code(submission_data: SubmissionSchema):
    submission_data = submission_data.model_dump()
    problem_submissions = submission_data["problems"]

    test_result = []
    score = 0

    for problem_submission in problem_submissions:
        problem = await retrieve_problem(problem_submission.problem_id)
        if not problem:
            logger.error(
                f"Problem with ID {problem_submission.problem_id} not found.")
            return ErrorResponseModel(error="An error occurred.",
                                      message="Problem not found.",
                                      code=404)
        problem_code = problem_submission.code

        public_testcases = problem.get("public_testcases", [])
        private_testcases = problem.get("private_testcases", [])

        def run_testcases(code, testcases, return_testcase):
            if not testcases:
                return []
            results_dict = test_py_funct(py_func=code,
                                         testcases=testcases,
                                         return_testcase=return_testcase)

            if results_dict["error"] is not None:
                return ErrorResponseModel(
                    error="Error running code.",
                    message=results_dict["error"],
                    code=500
                )
            return results_dict["testcase_outputs"]

        public_results = run_testcases(problem_code, public_testcases, True)
        if isinstance(public_results, ErrorResponseModel):
            return public_results

        private_results = run_testcases(problem_code, private_testcases, True)
        if isinstance(private_results, ErrorResponseModel):
            return private_results

        is_pass_problem = False
        if pass_testcases(public_results) and pass_testcases(private_results):
            score += 1
            is_pass_problem = True

        test_result.append(
            {
                "problem_id": problem_submission.problem_id,
                "public_testcases_results": public_results,
                "private_testcases_results": private_results,
                "is_pass_problem": is_pass_problem
            }
        )
    submission_data["test_result"] = test_result
    await add_submission(submission_data)

    return ResponseModel(
        data={
            "total_problem": len(problem_submissions),
            "score": score
        },
        message="Submission added successfully.",
        code=200)
