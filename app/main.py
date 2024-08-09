import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import LogProcessAndTime
from app.core.config import settings
from app.api.v1 import router as v1_router
from app.utils.logger import Logger
load_dotenv()

def create_application() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME,
                  #   openapi_url="/api/v1/openapi.json",
                  #   docs_url="/api/v1/docs"
                  )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LogProcessAndTime)
    app.include_router(v1_router, prefix="/api/v1")
    return app

app = create_application()
