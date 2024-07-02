from fastapi import APIRouter, Depends
from app.api.v1.routes.build_chart import router as build_chart_router
from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.problem import router as problem_router
from app.api.v1.routes.code import router as code_router
from app.api.v1.routes.submission import router as submission_router
from app.api.v1.routes.do_exam import router as do_exam_router
from app.core.security import (
    is_authenticated,
    is_aio
)

v1_router = APIRouter(prefix="/v1", tags=["API v1"])


@v1_router.get("/health")
async def check_health():
    return {"status": "API v1 is healthy"}

v1_router.include_router(build_chart_router,
                         dependencies=[Depends(is_authenticated)],
                         tags=["Build Chart"])

v1_router.include_router(user_router,
                         dependencies=[Depends(is_authenticated)],
                         tags=["User"])

v1_router.include_router(problem_router,
                        #  dependencies=[Depends(is_aio)],
                         dependencies=[Depends(is_authenticated)],
                         tags=["Problem"])

v1_router.include_router(code_router,
                         prefix="/code",
                        #  dependencies=[Depends(is_aio)],
                         dependencies=[Depends(is_authenticated)],
                         tags=["Code"])

v1_router.include_router(submission_router,
                         prefix="/submission",
                        #  dependencies=[Depends(is_aio)],
                         dependencies=[Depends(is_authenticated)],

                         tags=["Submission"])

v1_router.include_router(do_exam_router,
                         prefix="/time",
                        #  dependencies=[Depends(is_aio)],
                         dependencies=[Depends(is_authenticated)],
                         tags=["Do Exam Timer"])
