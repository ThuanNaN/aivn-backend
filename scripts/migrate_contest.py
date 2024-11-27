from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm
from pymongo import UpdateOne

try:
    contest_collection = mongo_db["contests"]
except Exception as e:
    exit(1)


async def add_cohort_field():
    add_data = []
    async for contest_data in contest_collection.find():
        add_data.append(contest_data)
    
    operators = []
    with tqdm(total=len(add_data)) as pbar:
        for index, contest_data in enumerate(add_data):
            operators.append(UpdateOne(
                {"_id": contest_data["_id"]},
                {"$set": {
                    "cohort": [2024],
                }}
            ))
            pbar.update(1)
    if operators:
        results = await contest_collection.bulk_write(operators)
        print(f"Modified {results.modified_count} documents")

    print("Done")

if __name__ == "__main__":
    asyncio.run(add_cohort_field())