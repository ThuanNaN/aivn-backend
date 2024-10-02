from app.core.database import mongo_db
import asyncio
from tqdm.asyncio import tqdm
from app.utils.generate import generate_id

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
            new_id = generate_id()
            while await certificate_collection.find_one({"validation_id": new_id}):
                new_id = generate_id()
            updated_cert = await certificate_collection.update_one(
                {"_id": cert["_id"]}, 
                {"$set": {
                    "validation_id": new_id
                }}
            )
            if updated_cert.modified_count == 0:
                print("Failed to update certificate with ID: ", cert["_id"])
            pbar.update(1)
    print("Done")

    certificate = []
    async for cert in certificate_collection.find():
        certificate.append(cert)

    certificate = [cer["validation_id"] for cer in certificate]
    # Check duplicates
    if len(certificate) != len(set(certificate)):
        print("Duplicates found")
    else:
        print("No duplicates found")

if __name__ == "__main__":
    asyncio.run(main())
