import asyncio
from app.api.v1.controllers.contest import contest_collection

async def main():
    result = await contest_collection.update_many(
        {},
        {"$set": {
            "instruction": "Details and instruction for the contest.", 
            "certificate_template": None
            }
        }
    )
    print(f"Modified {result.modified_count} documents")

if __name__ == "__main__":
    asyncio.run(main())