import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "aivnlearning"
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    ENV_TYPE: str = os.getenv("ENV_TYPE")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")
    OPENAPI_URL: str | None = "/v1/openapi.json" if ENV_TYPE == "development" else None
    DOCS_URL: str | None = "/v1/docs" if ENV_TYPE == "development" else None

settings = Settings()