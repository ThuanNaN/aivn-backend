from app.core.database import mongo_db
import asyncio
from bson.objectid import ObjectId
from app.utils.time import utc_to_local
from tqdm.asyncio import tqdm

try:
    submission_collection = mongo_db["submissions"]
except Exception as e:
    exit(1)



# submission helper
def submission_helper(submission) -> dict:
    retake_id = submission.get("retake_id", None)
    retake_id = str(retake_id) if retake_id else None
    return {
        "id": str(submission["_id"]),
        "exam_id": str(submission["exam_id"]),
        "clerk_user_id": submission["clerk_user_id"],
        "retake_id": retake_id,
        "submitted_problems": submission["submitted_problems"],
        "total_problems": submission["total_problems"],
        "created_at": utc_to_local(submission["created_at"]),

        # Missing fields
        "max_score": submission["max_score"] if "max_score" in submission else 50,
        "total_score": submission["total_score"],
    }


async def update_submission_schemas(exam_id: str) -> None:
    async for submission in tqdm(submission_collection.find({"exam_id": ObjectId(exam_id)}), 
                                 desc="Updating submissions"):

        total_problems_passed = submission.pop("total_score", 0)
        if total_problems_passed is None:
            total_problems_passed = 0
        max_score = 1000
        total_score = min(total_problems_passed*20 , max_score)

        new_submission = {
            **submission,
            "total_problems_passed": total_problems_passed,
            "total_score": total_score,
            "max_score": max_score
        }

        updated_submission = await submission_collection.update_one(
            {"_id": submission["_id"]}, {"$set": new_submission}
        )
        if updated_submission.modified_count > 0:
            print(f"Updated submission: {submission['_id']}")


async def check_max_score(exam_id: str) -> None:
    async for submission in tqdm(submission_collection.find({"exam_id": ObjectId(exam_id)}), 
                                 desc="Check schemas submissions"):
        if "max_score" not in submission:
            print(f"Submission {submission['_id']} doesn't have max_score field")
            print(submission)
            print()
        if "total_score" not in submission:
            print(f"Submission {submission['_id']} doesn't have total_score field")
            print(submission)
            print()


async def main():
    # Module 2 contest
    exam_id = "66bcd6d15a633824313da96c"

    print("Updating submission schemas")
    await update_submission_schemas(exam_id)

    print("Checking max_score field")
    await check_max_score(exam_id)

if __name__ == "__main__":
    asyncio.run(main())
