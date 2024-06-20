import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
from app.utils.logger import Logger
load_dotenv()
logger = Logger("core/database", log_file="database.log")

try:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'), uuidRepresentation="standard")
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

logger.info(f"URI: {os.getenv('MONGODB_URI')}")
logger.info(f"Database: {os.getenv('MONGODB_DB')}")