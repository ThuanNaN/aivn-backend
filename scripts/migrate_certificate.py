import traceback
from app.core.database import mongo_db
import asyncio
from pymongo import UpdateOne


try:
    certificate_collection = mongo_db["certificate"]
except Exception as e:
    exit(1)


async def delete_all_certificate() -> None:
    try:
        await certificate_collection.delete_many({})
        print("All certificates have been deleted")
    except Exception as e:
        print(f"{traceback.format_exc()}")


async def add_template_field():
    add_data = []
    async for certificate_data in certificate_collection.find():
        add_data.append(certificate_data)
    
    operators = []
    for index, certificate_data in enumerate(add_data):
        operators.append(UpdateOne(
            {"_id": certificate_data["_id"]},
            {"$set": {
                "template": "foundation",
            }}
        ))
    if operators:
        results = await certificate_collection.bulk_write(operators)
        print(f"Modified {results.modified_count} documents")

    print("Done")

if __name__ == "__main__":
    # asyncio.run(delete_all_certificate())
    asyncio.run(add_template_field())