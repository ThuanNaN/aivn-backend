from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import LogProcessAndTime
from app.core.config import settings
from app.api.v1 import router as v1_router
from prometheus_fastapi_instrumentator import Instrumentator
import inngest.fast_api
from app.inngest.client import inngest_client
from app.inngest import inngest_functions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load something
    yield
    # Clean up
    pass


def create_application() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME,
                  openapi_url=settings.OPENAPI_URL,
                  docs_url=settings.DOCS_URL,
                  lifespan=lifespan)
    allow_origins = [settings.FRONTEND_URL] if settings.ENV_TYPE == "production" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LogProcessAndTime)
    app.include_router(v1_router, prefix="/v1")
    return app

app = create_application()
Instrumentator().instrument(app).expose(app)
inngest.fast_api.serve(app, inngest_client, inngest_functions)
