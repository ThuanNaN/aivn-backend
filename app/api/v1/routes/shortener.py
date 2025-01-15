from datetime import datetime, UTC
from app.utils.logger import Logger
from fastapi import (
    APIRouter,Depends,
    HTTPException, status,
)
from app.api.v1.controllers.shortener import (
    add_short_url,
    retrieve_original_url,
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel
)
from app.schemas.shortener import (
    ShortenerSchema,
    ShortenerSchemaDB
)
from app.core.security import is_admin, is_authenticated

router = APIRouter()
logger = Logger("routes/shortener", log_file="shotener.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new short url")
async def create_short_url(shorten_data: ShortenerSchema, clerk_user_id=Depends(is_authenticated)):
    shorten_dict = ShortenerSchemaDB(
        **shorten_data.model_dump(),
        creator_id=clerk_user_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    ).model_dump()
    new_shorten = await add_short_url(shorten_dict)

    if isinstance(new_shorten, Exception):
        raise HTTPException(
            status_code=new_shorten.status_code,
            detail=new_shorten.message
        )
    return DictResponseModel(data=new_shorten, 
                             message="Short url added successfully",
                             code=status.HTTP_201_CREATED)


@router.get("/{original_url:path}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a short url by given original url")
async def get_original_url(short_url: str):
    original_url = await retrieve_original_url(short_url)
    if isinstance(original_url, Exception):
        raise HTTPException(
            status_code=original_url.status_code,
            detail=original_url.message
        )
    return DictResponseModel(data=original_url, 
                             message="Original url retrieved successfully",
                             code=status.HTTP_200_OK)

