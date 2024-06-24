from app.core.database import mongo_db
from app.utils.logger import Logger
from app.api.v1.controllers.run_code import test_py_funct

logger = Logger("controllers/submission", log_file="submission.log")

try:
    submission_collection = mongo_db["submissions"]
except Exception as e:
    logger.error(f"Error when connect to submissions: {e}")
    exit(1)


# helper
def submission_helper(submission) -> dict:
    return {
        "id": str(submission["_id"]),
        "user_id": submission["user_id"],
        "problems": submission["problems"],
        "created_at": str( submission["created_at"]),
    }

# Create a new submission
async def add_submission(submission_data: dict):
    try:
        submission = await submission_collection.insert_one(submission_data)
        new_submission = await submission_collection.find_one({"_id": submission.inserted_id})
        return submission_helper(new_submission)
    except Exception as e:
        logger.error(f"Error when add submission: {e}")


# Retrieve all submissions
async def retrieve_submissions():
    try:
        submissions = []
        async for submission in submission_collection.find():
            submissions.append(submission_helper(submission))
        return submissions
    except Exception as e:
        logger.error(f"Error when retrieve submissions: {e}")


def run_testcases(code, testcases):
    if not testcases:
        return [], True
    results_dict = test_py_funct(py_func=code,
                                    testcases=testcases,
                                    return_testcase=True,
                                    run_all=True)
    return_dict = []
    is_pass_testcases = True
    for result in results_dict["testcase_outputs"]:
        return_dict.append(
            {
                "input": result["input"],
                "output": result["output"],
                "expected_output": result["expected_output"],
                "error": result["error"],
                "is_pass": result["is_pass"]
            }
        )
        
        if not result["is_pass"]:
            is_pass_testcases = False

    return return_dict, is_pass_testcases
