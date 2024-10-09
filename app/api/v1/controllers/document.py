import traceback
from app.utils.time import utc_to_local
from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId

logger = Logger("controllers/document", log_file="document.log")
try:
    document_collection = mongo_db["documents"]
except Exception as e:
    logger.error(f"Error when connect to exam: {e}")
    exit(1)


# helper
def document_helper(meeting: dict) -> dict:
    return {
        "id": str(meeting["_id"]),
        "file_name": meeting["file_name"],
        "meeting_id": str(meeting["meeting_id"]),
        "mask_url": meeting["mask_url"],
        "creator_id": meeting["creator_id"],
        "created_at": utc_to_local(meeting["created_at"]),
        "updated_at": utc_to_local(meeting["updated_at"])
    }


async def add_document(document_data: dict) -> dict:
    """
    Add a new document to database

    :param document_data: dict

    :return: dict
    """
    try:
        document_data["meeting_id"] = ObjectId(document_data["meeting_id"])
        document = await document_collection.insert_one(document_data)
        new_document = await document_collection.find_one({"_id": document.inserted_id})
        return document_helper(new_document)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_documents() -> list[dict]:
    """
    Retrieve all documents in database

    :return: list[dict]
    """
    try:
        documents = []
        async for document in document_collection.find():
            documents.append(document_helper(document))
        return documents
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def retrieve_document_by_id(id: str) -> dict:
    """
    Retrieve a document with a matching ID

    :param id: str

    :return: dict
    """
    try:
        document = await document_collection.find_one({"_id": ObjectId(id)})
        if document:
            return document_helper(document)
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
    

async def retrieve_document_by_meeting_id(meeting_id: str) -> list[dict]:
    """
    Retrieve all documents with a matching meeting ID

    :param meeting_id: str

    :return: list[dict]
    """
    try:
        documents = []
        async for document in document_collection.find({"meeting_id": ObjectId(meeting_id)}):
            documents.append(document_helper(document))
        return documents
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def update_document(id: str, data: dict) -> dict:
    """
    Update a document with a matching ID

    :param id: str
    :param data: dict

    :return: dict
    """
    try:
        document = await document_collection.find_one({"_id": ObjectId(id)})
        if not document:
            raise Exception("Document not found")
        
        data["meeting_id"] = ObjectId(data["meeting_id"])
        updated_document = await document_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        
        if updated_document.modified_count == 1:
            document = await document_collection.find_one({"_id": ObjectId(id)})
            return document_helper(document)
        raise Exception("Document could not be updated")
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_document_by_id(id: str) -> bool:
    """
    Delete a document with a matching ID

    :param id: str

    :return: dict
    """
    try:
        document = await document_collection.find_one({"_id": ObjectId(id)})
        if not document:
            raise Exception("Document not found")
        deleted_info = await document_collection.delete_one({"_id": ObjectId(id)})
        if deleted_info.deleted_count == 1:
            return True
        raise Exception("Document could not be deleted")
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e


async def delete_documents_by_meeting_id(meeting_id: str) -> bool:
    """
    Delete all documents with a matching meeting ID

    :param meeting_id: str

    :return: dict
    """
    try:
        deleted_info = await document_collection.delete_many(
            {"meeting_id": ObjectId(meeting_id)}
        )
        if deleted_info.deleted_count >= 1:
            return True
        raise Exception("Documents could not be deleted")
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        return e
