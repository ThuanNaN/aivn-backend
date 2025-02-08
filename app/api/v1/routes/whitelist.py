from typing import Optional, List
from datetime import datetime, UTC
from app.utils import Logger, MessageException
import pandas as pd
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    UploadFile,
    Query,
    HTTPException, status
)
from app.api.v1.controllers.whitelist import (
    retrieve_all_whitelists,
    retrieve_whitelist_by_pipeline,
    add_whitelist,
    update_whitelist_by_id,
    delete_whitelist_by_id,
    upsert_whitelist,
)
from app.schemas.whitelist import (
    WhiteListSchema,
    WhiteListSchemaDB,
    UpdateWhiteList,
    UpdateWhiteListDB
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel
)

router = APIRouter()
logger = Logger("routes/whitelist", log_file="whitelist.log")


async def read_csv(file: UploadFile):
    content = await file.read()
    csv_data = content.decode('utf-8-sig')
    csv_reader = csv.reader(StringIO(csv_data))
    return csv_reader


@router.get("/whitelists",
            tags=["Admin"],
            description="Retrieve all whitelists with matching search and filter")
async def get_whitelists(
    search: str | None = Query(None, description="Search by problem title or description"),
    cohort: int | None = Query(None, description="Filter by cohort"),
    is_auditor: bool = Query(False, description="Filter by auditor"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"nickname": {"$regex": search, "$options": "i"}},
        ]
    if cohort is not None:
        match_stage["$match"]["cohort"] = cohort

    if is_auditor:
        match_stage["$match"]["is_auditor"] = is_auditor
        
    pipeline = [
        match_stage,
        {
            "$facet": {
                "whitelists": [
                    {
                        "$skip": (page - 1) * per_page
                    },
                    {
                        "$limit": per_page
                    }
                ],
                "total": [
                    {
                        "$count": "count"
                    }
                ]
            }
        },
    ]
    whitelists = await retrieve_whitelist_by_pipeline(pipeline, page, per_page)
    if isinstance(whitelists, MessageException):
        raise HTTPException(
            status_code=whitelists.status_code,
            detail=whitelists.message
        )
    return DictResponseModel(
        data=whitelists,
        message="Whitelists retrieved successfully.",
        code=status.HTTP_200_OK
    )


@router.post("",
             tags=["Admin"],
             description="Add a new whitelist.")
async def add_whitelist_data(whitelist: WhiteListSchema):
    whitelist_data = WhiteListSchemaDB(
        **whitelist.model_dump(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    ).model_dump()

    new_whitelist = await add_whitelist(whitelist_data)
    if isinstance(new_whitelist, MessageException):
        raise HTTPException(
            status_code=new_whitelist.status_code,
            detail=new_whitelist.message
        )
    return DictResponseModel(
        data=new_whitelist,
        message="Whitelist added successfully.",
        code=status.HTTP_201_CREATED
    )


@router.post("/import",
            tags=["Admin"],
            description="Import a whitelist via csv file")
async def import_whitelist_csv(whitelists: List[WhiteListSchema],
                               remove_not_exist: Optional[bool] = Query(False)):    
    whitelists_data = [WhiteListSchemaDB(
        **data.model_dump(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    ).model_dump() for data in whitelists]
    upsert_result = await upsert_whitelist(whitelists_data, remove_not_exist)
    if isinstance(upsert_result, MessageException):
        raise HTTPException(
            status_code=upsert_result.status_code,
            detail=upsert_result.message
        )
    return ListResponseModel(data=[],
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)


@router.patch("/{id}",
              tags=["Admin"],
              description="Update a whitelist.")
async def update_whitelist_data(
    id: str,
    data: UpdateWhiteList
):
    whitelist_data = UpdateWhiteListDB(
        **data.model_dump(),
        updated_at=datetime.now(UTC)
    ).model_dump()
    updated_whitelist = await update_whitelist_by_id(id, whitelist_data)
    if isinstance(updated_whitelist, MessageException):
        raise HTTPException(
            status_code=updated_whitelist.status_code,
            detail=updated_whitelist.message
        )
    return DictResponseModel(
        data=updated_whitelist,
        message="Whitelist updated successfully.",
        code=status.HTTP_200_OK
    )


@router.delete("/{id}",
               tags=["Admin"],
               description="Delete a whitelist with a matching id")
async def delete_whitelist(id: str):
    deleted = await delete_whitelist_by_id(id)
    if isinstance(deleted, MessageException):
        raise HTTPException(
            status_code=deleted.status_code,
            detail=deleted.message
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not deleted."
        )
    return ListResponseModel(data=[],
                             message="User deleted successfully.",
                             code=status.HTTP_200_OK)


@router.get("/export",
            tags=["Admin"],
            description="Export a whitelist via csv file")
async def export_whitelist_csv():
    whitelist_data = await retrieve_all_whitelists()
    if isinstance(whitelist_data, MessageException):
        raise HTTPException(
            status_code=whitelist_data.status_code,
            detail=whitelist_data.message
        )
    
    df = pd.DataFrame(whitelist_data)
    df = df.loc[:, ["id", "email", "cohort", "nickname", "created_at", "updated_at"]]

    output = StringIO()
    df.to_csv(output, index=False, encoding='ascii', errors='replace')
    output.seek(0)
    return StreamingResponse(output,
                             media_type="text/csv",
                             headers={"Content-Disposition": "attachment;filename=whitelist.csv"})

