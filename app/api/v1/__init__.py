from fastapi import APIRouter, Depends
from app.api.v1.routes.visualize import router as visualize_router
from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.contest import router as contest_router
from app.api.v1.routes.exam import router as exam_router
from app.api.v1.routes.category import router as category_router
from app.api.v1.routes.problem import router as problem_router
from app.api.v1.routes.code import router as code_router
from app.api.v1.routes.submission import router as submission_router
from app.api.v1.routes.retake import router as retake_router
from app.api.v1.routes.sleep import router as sleep_router
from app.core.security import (
    is_authenticated,
    is_aio,
    is_admin
)

router = APIRouter()

router.include_router(visualize_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/visualize",
                      tags=["Visualize"])

router.include_router(user_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/user",
                      tags=["User"])

router.include_router(contest_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/contest",
                      tags=["Contest"])

router.include_router(exam_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/exam",
                      tags=["Exam"])

router.include_router(category_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/category",
                      tags=["Category"])

router.include_router(problem_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/problem",
                      tags=["Problem"])

router.include_router(code_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/code",
                      tags=["Code"])

router.include_router(submission_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/submission",
                      tags=["Submission"])

router.include_router(retake_router,
                      dependencies=[Depends(is_admin)],
                      prefix="/retake",
                      tags=["Retake"])

router.include_router(sleep_router,
                      dependencies=[Depends(is_admin)],
                      prefix="/sleep",
                      tags=["Sleep"])
