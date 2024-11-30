import traceback
from app.utils import utc_to_local, MessageException, Logger
from fastapi import status
from app.core.database import mongo_db
from bson.objectid import ObjectId


logger = Logger("controllers/certificate", log_file="certificate.log")

try:
    certificate_collection = mongo_db["certificate"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper
def certificate_helper(certificate) -> dict:
    return {
        "id": str(certificate["_id"]),
        "validation_id": certificate["validation_id"],
        "clerk_user_id": certificate["clerk_user_id"],
        "submission_id": certificate["submission_id"],
        "result_score": certificate["result_score"],
        "created_at": utc_to_local(certificate["created_at"]),
    }


async def add_certificate(certificate_data: dict) -> dict:
    """
    Create a new certificate
    :param certificate_data: dict
    :return: dict
    """
    try:
        certificate = await certificate_collection.insert_one(certificate_data)
        new_certificate = await certificate_collection.find_one({"_id": certificate.inserted_id})
        return certificate_helper(new_certificate)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add certificate", 
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

async def retrieve_certificates() -> list[dict]:
    """
    Retrieve all certificates in database
    :return: list[dict]
    """
    try:
        certificate_list = []
        async for certificate in certificate_collection.find():
            certificate_list.append(certificate_helper(certificate))
        return certificate_list

    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve certificates",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def retrieve_certificates_by_clerk_user_id(clerk_user_id: str) -> list[dict]:
    """
    Retrieve all certificates by clerk_user_id in database
    :clerk_user_id: str
    :return: list[dict]
    """
    try:
        certificate_list = []
        async for certificate in certificate_collection.find({"clerk_user_id": clerk_user_id}):
            certificate_list.append(certificate_helper(certificate))
        return certificate_list
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve certificates",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

async def retrieve_certificate_by_submission_id(submission_id: str) -> dict:
    """
    Retrieve certificate by submission_id
    :submission_id: str
    :return: dict
    """
    try:
        certificate = await certificate_collection.find_one({"submission_id": submission_id})
        if certificate:
            return certificate_helper(certificate)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve certificate",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_certificate_by_validation_id(validation_id: str) -> dict:
    """
    Retrieve certificate by validation_id
    :validation_id: str
    :return: dict
    """
    try:
        certificate = await certificate_collection.find_one(
            {"validation_id": validation_id}
        )
        if certificate:
            return certificate_helper(certificate)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve certificate",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    

async def update_certificate(id: str, data: dict) -> dict:
    """
    Update a certificate with a matching ID
    :param id: str
    :param data: dict
    :return: dict
    """
    try:
        certificate = await certificate_collection.find_one({"_id": ObjectId(id)})
        if certificate:
            updated_certificate = await certificate_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated_certificate.modified_count == 0:
                raise MessageException("Update certificate failed",
                                       status.HTTP_400_BAD_REQUEST)
            return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update certificate",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_certificate(id: str) -> dict:
    """
    Delete a certificate with a matching ID
    :param id: str
    :return: dict
    """
    try:
        certificate = await certificate_collection.find_one({"_id": ObjectId(id)})
        if not certificate:
            raise MessageException("Certificate not found",
                                   status.HTTP_404_NOT_FOUND)
        delete_certificate = await certificate_collection.delete_one({"_id": ObjectId(id)})
        if delete_certificate.deleted_count == 0:
            raise MessageException("Delete certificate failed",
                                    status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete certificate",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)

