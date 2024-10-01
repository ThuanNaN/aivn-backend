import asyncio
from slugify import slugify
from app.api.v1.controllers.contest import contest_collection

async def main():
    result = await contest_collection.update_many(
        {},
        {"$set": {
            "instruction": "Details and instruction for the contest.", 
            "certificate_template": None,
            }
        }
    )
    print(f"Modified {result.modified_count} documents")


async def upsert_slug():
    contest_info = []
    async for contest in contest_collection.find():
        contest["slug"] = slugify(contest["title"])
        contest_info.append(contest)

    for contest in contest_info:
        await contest_collection.update_one(
            {"_id": contest["_id"]},
            {"$set": {
                "slug": contest["slug"]
            }}
        )
    print("Slug updated")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(upsert_slug())