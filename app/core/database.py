import os
import asyncio
import motor.motor_asyncio
from app.core.config import settings
from app.utils.logger import Logger
logger = Logger("core/database", log_file="database.log")

try:
    MONGODB_URI = settings.MONGODB_URI
    logger.info("Connecting to MongoDB")
    logger.info(f"MongoDB URI: {MONGODB_URI}")
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI, 
                                                          uuidRepresentation="standard")
    conn = mongo_client.admin.command('ping')
    mongo_client.get_io_loop = asyncio.get_running_loop
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"An error occurred while trying to connect to MongoDB: {e}")


try:
    mongo_db = mongo_client[os.getenv('MONGODB_DB')]
    logger.info("Connected to Database")
except Exception as e:
    logger.error(f"An error occurred while trying to connect to Database: {e}")
    exit(1)