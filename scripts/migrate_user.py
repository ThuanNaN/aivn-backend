from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm
from pymongo import UpdateOne

try:
    user_collection = mongo_db["users"]
except Exception as e:
    exit(1)


async def add_attend_id():
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
        update_results = await user_collection.bulk_write(operators)
        print(update_results)

    print("Done")


async def add_cohort_field():
    users = []
    async for user in user_collection.find():
        users.append(user)

    print(f"Find {len(users)} users")
    
    operators = []
    with tqdm(total=len(users)) as pbar:
        for index, user in enumerate(users):
            if "cohort" not in user:
                operators.append(UpdateOne(
                    {"_id": user["_id"]},
                    {"$set": {
                        "cohort": 0
                    }}
                ))
            pbar.update(1)
    if operators:
        update_results = await user_collection.bulk_write(operators)
        print(update_results)

    print("Done")


async def add_feasible_cohort():
    users = []
    async for user in user_collection.find():
        users.append(user)

    print(f"Find {len(users)} users")
    
    operators = []
    with tqdm(total=len(users)) as pbar:
        for index, user in enumerate(users):
            if "feasible_cohort" not in user:
                operators.append(UpdateOne(
                    {"_id": user["_id"]},
                    {"$set": {
                        "feasible_cohort": [user["cohort"]]
                    }}
                ))
            pbar.update(1)
    if operators:
        update_results = await user_collection.bulk_write(operators)
        print(update_results)

    print("Done")


if __name__ == "__main__":
    # asyncio.run(add_attend_id())
    # asyncio.run(add_cohort_field())
    asyncio.run(add_feasible_cohort())
