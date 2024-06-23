from fastapi import APIRouter, Body
from app.schemas.submission import SubmissionSchema, ResponseModel
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.run_code import test_py_funct
from app.api.v1.controllers.submission import add_submission
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/submission", log_file="submission.log")


@router.post("/submit", description="Submit code to a test")
async def submit_code(submission_data: SubmissionSchema):
    submission_data = submission_data.model_dump()
    problem_submissions = submission_data["problems"]

    test_result = []

    for problem_submission in problem_submissions:
        problem = await retrieve_problem(problem_submission.problem_id)
        code = problem_submission.code

        public_testcases = problem["public_testcases"]
        private_testcases = problem["private_testcases"]

        # Run code
        public_testcases_results = test_py_funct(code, public_testcases)
        private_testcases_results = test_py_funct(code, private_testcases)
        
        test_result.append(
            {
                "problem_id": problem_submission.problem_id,
                "public_testcases_results": public_testcases_results,
                "private_testcases_results": private_testcases_results,
            }
        )
    submission_data["test_result"] = test_result
    new_submission = await add_submission(submission_data)
    return ResponseModel(data=new_submission,
                         message="Submission added successfully.",
                         code=200)
