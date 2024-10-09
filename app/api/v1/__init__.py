from app.core.config import settings
from fastapi import APIRouter, Depends
from app.api.v1.routes.visualize import router as visualize_router
from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.meeting import router as meeting_router
from app.api.v1.routes.document import router as document_router
from app.api.v1.routes.contest import router as contest_router
from app.api.v1.routes.exam import router as exam_router
from app.api.v1.routes.category import router as category_router
from app.api.v1.routes.problem import router as problem_router
from app.api.v1.routes.code import router as code_router
from app.api.v1.routes.submission import router as submission_router
from app.api.v1.routes.retake import router as retake_router
from app.api.v1.routes.verify import router as verify_router
from app.api.v1.routes.sleep import router as sleep_router
from app.core.security import (
    is_authenticated,
    is_aio,
    is_admin
)
router = APIRouter()

# Public User Routes
router.include_router(visualize_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/visualize",
                      tags=["Visualize"])

router.include_router(user_router,
                      dependencies=[Depends(is_authenticated)],
                      prefix="/user",
                      tags=["User"])

router.include_router(verify_router,
                      prefix="/verify",
                      tags=["Verify"])

# Admin Routes
router.include_router(retake_router,
                      dependencies=[Depends(is_admin)],
                      prefix="/retake",
                      tags=["Retake"])

router.include_router(sleep_router,
                      dependencies=[Depends(is_admin)],
                      prefix="/sleep",
                      tags=["Sleep"])

# Dev (admin only) Routes
if settings.ENV_TYPE == "development":
    AIO_DEPENDENCIES = [Depends(is_admin)]

# Production Routes
elif settings.ENV_TYPE == "production":
    AIO_DEPENDENCIES = [Depends(is_aio)]

else:
    raise ValueError("Invalid Environment Type in .env file")

router.include_router(contest_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/contest",
                      tags=["Contest"])

router.include_router(exam_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/exam",
                      tags=["Exam"])

router.include_router(category_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/category",
                      tags=["Category"])

router.include_router(problem_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/problem",
                      tags=["Problem"])

router.include_router(code_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/code",
                      tags=["Code"])

router.include_router(submission_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/submission",
                      tags=["Submission"])

router.include_router(meeting_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/meeting",
                      tags=["Meeting"])

router.include_router(document_router,
                      dependencies=AIO_DEPENDENCIES,
                      prefix="/document",
                      tags=["Document"])