import traceback
from app.utils.logger import Logger
from fastapi import (
    APIRouter,
    status,
    HTTPException
)
from app.api.v1.controllers.certificate import (
    retrieve_certificate_by_validation_id
)
from app.api.v1.controllers.user import (
    retrieve_user
)

from app.schemas.response import (
    DictResponseModel
)

router = APIRouter()
logger = Logger("routes/verify", log_file="verify.log")


@router.get("/certificate/{validation_id}",
            description="Get certificate by validation id")
async def get_certificate_by_validation_id(validation_id: str):
    try:
        certificate = await retrieve_certificate_by_validation_id(validation_id)
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        user_info = await retrieve_user(certificate["clerk_user_id"])

        return_data = {
            **certificate,
            "fullname": user_info["fullname"],
        }

        return DictResponseModel(data=return_data,
                                 message="Certificate retrieved successfully",
                                 code=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
