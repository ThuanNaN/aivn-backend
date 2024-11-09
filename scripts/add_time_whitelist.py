from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm
from pymongo import UpdateOne
from datetime import datetime, UTC

try:
    whitelist_collection = mongo_db["whitelists"]
except Exception as e:
    exit(1)


async def main():
    all_data = []
    async for data in whitelist_collection.find():
        all_data.append(data)
    
    operators = []
    with tqdm(total=len(all_data)) as pbar:
        for index, data in enumerate(all_data):
            operators.append(UpdateOne(
                {"_id": data["_id"]},
                {"$set": {
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC)
                }}
            ))
        pbar.update(1)
    if operators:
        await whitelist_collection.bulk_write(operators)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())