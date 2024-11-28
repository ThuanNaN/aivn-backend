import traceback
from app.utils import (
    Logger, 
    MessageException, 
    convert_objectid_to_str,
    convert_id_to_id
)
from fastapi import APIRouter, status, Depends
from app.api.v1.controllers.submission import (
    retrieve_submissions,
    retrieve_submission_by_pipeline
)
from app.api.v1.controllers.retake import (
    retrieve_retakes,
    retrieve_retakes_unsubmit
)
from app.schemas.response import ListResponseModel
from app.core.security import is_admin


router = APIRouter()
logger = Logger("routes/retake", log_file="retake.log")

@router.get("/{unsubmit}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all retakes that have not been submitted")
async def get_retakes_unsubmit(unsubmit: bool = True):
    try:
        if not unsubmit:
            retakes_data = await retrieve_retakes()
        else:
            pipeline = [
                {
                    "$match": {
                        "retake_id": {"$ne": None}
                    }
                },

                {
                    "$group": {
                        "_id": "$retake_id",
                    }
                },
            ]
            submission_retake_ids = await retrieve_submission_by_pipeline(pipeline)
            submission_retake_ids = [data["_id"] for data in submission_retake_ids]

            retakes_data = await retrieve_retakes_unsubmit(submission_retake_ids)
            retakes_data = convert_objectid_to_str(retakes_data)
            retakes_data = convert_id_to_id(retakes_data)
        
        return ListResponseModel(data=retakes_data,
                                 message="Retakes unsubmit retrieved successfully",
                                 code=status.HTTP_200_OK)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve retakes unsubmit",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
