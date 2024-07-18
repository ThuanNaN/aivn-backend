from fastapi import APIRouter, Depends
from app.api.v1.routes.build_chart import router as build_chart_router
from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.contest import router as contest_router
from app.api.v1.routes.category import router as category_router
from app.api.v1.routes.problem import router as problem_router
from app.api.v1.routes.code import router as code_router
from app.api.v1.routes.timer import router as timer_router
from app.api.v1.routes.submission import router as submission_router
from app.core.security import (
    is_authenticated,
    is_aio
)

router = APIRouter()

# router.include_router(build_chart_router,
#                       dependencies=[Depends(is_authenticated)],
#                       prefix="/visualize",
#                       tags=["Visualize"])

router.include_router(user_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/user",
                      tags=["User"])


router.include_router(contest_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/contest",
                      tags=["Contest"])

router.include_router(category_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/category",
                      tags=["Category"])

router.include_router(problem_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/problem",
                      tags=["Problem"])


router.include_router(code_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/code",
                      tags=["Code"])


router.include_router(submission_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/submission",
                      tags=["Submission"])


router.include_router(timer_router,
                      #   dependencies=[Depends(is_authenticated)],
                      prefix="/time",
                      tags=["Timer"])
