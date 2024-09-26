import traceback
from app.core.database import mongo_db
import asyncio

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


async def main():
    await delete_all_certificate()

if __name__ == "__main__":
    asyncio.run(main())