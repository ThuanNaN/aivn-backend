from app.core.database import mongo_db
from app.utils.logger import Logger

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
        "test_result": submission["test_result"],
        "created_at": str( submission["created_at"]),
    }

# Create a new submission
async def add_submission(submission_data: dict) -> dict:
    try:
        submission = await submission_collection.insert_one(submission_data)
        new_submission = await submission_collection.find_one({"_id": submission.inserted_id})
        return submission_helper(new_submission)
    except Exception as e:
        logger.error(f"Error when add submission: {e}")

