from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm
from pymongo import UpdateOne

try:
    meeting_collection = mongo_db["meetings"]
except Exception as e:
    exit(1)


async def main():
    all_meeting_data = []
    async for meeting_data in meeting_collection.find():
        all_meeting_data.append(meeting_data)
    
    operators = []
    with tqdm(total=len(all_meeting_data)) as pbar:
        for index, meeting_data in enumerate(all_meeting_data):
            operators.append(UpdateOne(
                {"_id": meeting_data["_id"]},
                {"$set": {
                    "record": ""
                }}
            ))
            pbar.update(1)
    if operators:
        await meeting_collection.bulk_write(operators)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())