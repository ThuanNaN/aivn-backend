from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/problem", log_file="problem.log")

try:
    problem_collection = mongo_db["problems"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)

# helper
def problem_helper(problem) -> dict:
    return {
        "id": str(problem["_id"]),
        "title": problem["title"],
        "description": problem["description"],
        "index": problem["index"],
        "code_template": problem["code_template"],
        "public_testcases": problem["public_testcases"],
        "private_testcases": problem["private_testcases"],
        "created_at": str( problem["created_at"]),
        "updated_at": str(problem["updated_at"])
    }

# Create a new problem
async def add_problem(problem_data: dict) -> dict:
    try:
        problem = await problem_collection.insert_one(problem_data)
        new_problem = await problem_collection.find_one({"_id": problem.inserted_id})
        return problem_helper(new_problem)
    except Exception as e:
        logger.error(f"Error when add problem: {e}")


# Retrieve all problems
async def retrieve_problems():
    try:
        problems = []
        async for problem in problem_collection.find():
            problems.append(problem_helper(problem))
        return problems
    except Exception as e:
        print(f"Error when retrieve problems: {e}")
        logger.error(f"Error when retrieve problems: {e}")


# Retrieve a problem with a matching ID
async def retrieve_problem(id: str) -> dict:
    try:
        problem = await problem_collection.find_one({"_id": ObjectId(id)})
        if problem:
            return problem_helper(problem)
    except Exception as e:
        logger.error(f"Error when retrieve problem: {e}")


# Update a problem with a matching ID
async def update_problem(id: str, data: dict):
    try:
        if len(data) < 1:
            return False
        problem = await problem_collection.find_one({"_id": ObjectId(id)})
        if problem:
            updated_problem = await problem_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated_problem:
                return True
            return False
    except Exception as e:
        logger.error(f"Error when update problem: {e}")


# Delete a problem from the database
async def delete_problem(id: str):
    try:
        problem = await problem_collection
        if problem:
            await problem_collection.delete_one({"_id": ObjectId(id)})
            return True
    except Exception as e:
        logger.error(f"Error when delete problem: {e}")
