from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import LogProcessAndTime
from app.core.config import settings
from app.api.v1 import router as v1_router
from prometheus_fastapi_instrumentator import Instrumentator

def create_application() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME,
                  openapi_url=settings.OPENAPI_URL,
                  docs_url=settings.DOCS_URL)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONTEND_URL,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LogProcessAndTime)
    app.include_router(v1_router, prefix="/v1")
    return app

app = create_application()
instrumentator = Instrumentator().instrument(app)

@app.on_event("startup")
async def _startup():
    instrumentator.expose(app)
