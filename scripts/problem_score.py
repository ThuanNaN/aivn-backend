from app.core.database import mongo_db
import asyncio

try:
    problem_collection = mongo_db["problems"]
except Exception as e:
    exit(1)


async def missing_problem_score():
    problems = []
    async for doc in problem_collection.find():
        problems.append(doc)

    # Check problem score is exist in all problems
    for problem in problems:
        if 'problem_score' not in problem:
            print(problem['_id'], problem['title'])

    print("Finish!")


if __name__ == "__main__":
    asyncio.run(missing_problem_score())