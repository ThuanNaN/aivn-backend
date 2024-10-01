import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Python Coding API"
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    ENV_TYPE: str = os.getenv("ENV_TYPE")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")

settings = Settings()