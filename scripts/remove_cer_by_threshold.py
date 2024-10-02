from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm

try:
    certificate_collection = mongo_db["certificate"]
except Exception as e:
    exit(1)


async def main():
    certificate = []
    async for cert in certificate_collection.find():
        certificate.append(cert)
    
    with tqdm(total=len(certificate)) as pbar:
        for cert in certificate:
            score = int(cert["result_score"].split("/")[0])
            max_score = int(cert["result_score"].split("/")[1])

            if max_score == 0 or score/max_score < 0.5 :
                deleted = await certificate_collection.delete_one({"_id": cert["_id"]})
                if deleted.deleted_count == 0:
                    print("Failed to delete certificate with ID: ", cert["_id"])
                else:
                    print("Deleted certificate with ID: ", cert["_id"])
            pbar.update(1)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())