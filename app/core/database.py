import os
from dotenv import load_dotenv
import motor.motor_asyncio
load_dotenv()
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'), uuidRepresentation="standard")

try:
    conn = mongo_client.admin.command('ping')
    print("Connected to MongoDB")
except Exception as e:
    print(e)

try:
    mongo_db = mongo_client[os.getenv('MONGODB_DB')]
    print("Connected to Database")
except Exception as e:
    print(f"An error occurred while trying to access the database: {e}")
    exit(1)