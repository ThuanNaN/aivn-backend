from app.core.database import mongo_db
from app.utils.logger import Logger
from bson.objectid import ObjectId


logger = Logger("controllers/exam", log_file="exam.log")

try:
    exam_collection = mongo_db["exam"]
except Exception as e:
    logger.error(f"Error when connect to exam: {e}")
    exit(1)


#helper
def exam_helper(exam: dict) -> dict:
    return {
        "id": str(exam["_id"]),
        "contest_id": exam["contest_id"],
        "title": exam["title"],
        "description": exam["description"],
        "is_active": exam["is_active"],
        "created_at": exam["created_at"],
        "updated_at": exam["updated_at"]
    }


async def add_exam(exam_data: dict) -> dict:
    """
    Add a new exam to database
    :param exam_data: dict
    :return: dict
    """
    try:
        exam = await exam_collection.insert_one(exam_data)
        new_exam = await exam_collection.find_one({"_id": exam.inserted_id})
        return exam_helper(new_exam)
    except Exception as e:
        logger.error(f"Error when create exam: {e}")


async def retrieve_exams() -> list:
    """
    Retrieve all exams from database
    :return: list
    """
    try:
        exams = []
        async for exam in exam_collection.find():
            exams.append(exam_helper(exam))
        return exams
    except Exception as e:
        logger.error(f"Error when retrieve exams: {e}")


async def retrieve_exam(id: str) -> dict:
    """
    Retrieve a exam with a matching ID
    :param id: str
    :return: dict
    """
    try:
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if exam:
            return exam_helper(exam)
    except Exception as e:
        logger.error(f"Error when retrieve exam: {e}")


async def update_exam(id: str, data: dict) -> bool:
    """
    Update a exam with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            return False
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if exam:
            updated_exam = await exam_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": data}
            )
            if updated_exam:
                return True
            return False
    except Exception as e:
        logger.error(f"Error when update exam: {e}")


async def delete_exam(id: str) -> bool:
    """
    Delete a exam from database
    :param id: str
    :return: bool
    """
    try:
        exam = await exam_collection.find_one({"_id": ObjectId(id)})
        if exam:
            await exam_collection.delete_one({"_id": ObjectId(id)})
            return True
    except Exception as e:
        logger.error(f"Error when delete exam: {e}")
        return False