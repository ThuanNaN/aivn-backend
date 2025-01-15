import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "aivnlearning"
    ENV_TYPE: str = os.getenv("ENV_TYPE")
    OPENAPI_URL: str | None = "/v1/openapi.json" if ENV_TYPE == "development" else None
    DOCS_URL: str | None = "/v1/docs" if ENV_TYPE == "development" else None
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    INNGEST_SIGNING_KEY: str = os.getenv("INNGEST_SIGNING_KEY")
    INNGEST_EVENT_KEY: str = os.getenv("INNGEST_EVENT_KEY")


settings = Settings()