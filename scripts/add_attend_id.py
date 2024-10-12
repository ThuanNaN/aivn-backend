from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm
from pymongo import UpdateOne, DeleteOne, InsertOne

try:
    user_collection = mongo_db["users"]
except Exception as e:
    exit(1)


async def main():
    users = []
    async for user in user_collection.find():
        users.append(user)
    
    operators = []
    with tqdm(total=len(users)) as pbar:
        for index, user in enumerate(users):
            if "attend_id" not in user:
                new_id = str(index).zfill(4)
                operators.append(UpdateOne(
                    {"_id": user["_id"]},
                    {"$set": {
                        "attend_id": new_id
                    }}
                ))
            pbar.update(1)
    if operators:
        await user_collection.bulk_write(operators)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())