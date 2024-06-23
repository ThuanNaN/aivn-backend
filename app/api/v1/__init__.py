from fastapi import APIRouter
from app.api.v1.routes.build_chart import router as build_chart_router
from app.api.v1.routes.problem import router as problem_router
from app.api.v1.routes.code import router as code_router
from app.api.v1.routes.submission import router as submission_router

v1_router = APIRouter(prefix="/v1", tags=["API v1"])

@v1_router.get("/health")
async def check_health():
    return {"status": "API v1 is healthy"}

v1_router.include_router(build_chart_router, tags=["Build Chart"])
v1_router.include_router(problem_router, tags=["Problem"])
v1_router.include_router(code_router, prefix="/code", tags=["Code"])
v1_router.include_router(submission_router, prefix="/code", tags=["Code"])
