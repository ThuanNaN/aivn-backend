from typing import Optional, List
from datetime import datetime, UTC
from app.utils.logger import Logger
import pandas as pd
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    UploadFile,
    Query, Depends,
    HTTPException, status
)
from app.core.security import (
    is_admin
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
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all whitelists with matching search and filter")
async def get_whitelists(
    search: Optional[str] = Query(None, description="Search by problem title or description"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"nickname": {"$regex": search, "$options": "i"}},
        ]
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
    if isinstance(whitelists, Exception):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelists not found."
        )
    return DictResponseModel(
        data=whitelists,
        message="Whitelists retrieved successfully.",
        code=status.HTTP_200_OK
    )


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new whitelist.")
async def add_whitelist(whitelist: WhiteListSchema):
    whitelist_data = WhiteListSchemaDB(
        **whitelist.model_dump(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    new_whitelist = await add_whitelist(whitelist_data)
    if isinstance(new_whitelist, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Whitelist not added."
        )
    return DictResponseModel(
        data=new_whitelist,
        message="Whitelist added successfully.",
        code=status.HTTP_201_CREATED
    )


@router.post("/import/whitelist",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Import a whitelist via csv file")
async def import_whitelist_csv(whitelists: List[WhiteListSchema],
                               remove_not_exist: Optional[bool] = Query(False)):
    whitelists_data = [WhiteListSchemaDB(
        **data.model_dump(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    ).model_dump() for data in whitelists]
    whitelist = await upsert_whitelist(whitelists_data, remove_not_exist)
    if isinstance(whitelist, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    return ListResponseModel(data=[],
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)


@router.patch("/{id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a whitelist.")
async def update_whitelist_data(
    id: str,
    data: UpdateWhiteList
):
    whitelist_data = UpdateWhiteListDB(
        **data.model_dump(),
        updated_at=datetime.now(UTC)
    )
    updated_whitelist = await update_whitelist_by_id(id, whitelist_data)
    if isinstance(updated_whitelist, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Whitelist not updated."
        )
    return DictResponseModel(
        data=updated_whitelist,
        message="Whitelist updated successfully.",
        code=status.HTTP_200_OK
    )


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a whitelist with a matching id")
async def delete_whitelist(id: str):
    deleted = await delete_whitelist_by_id(id)
    if isinstance(deleted, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not deleted."
        )
    return ListResponseModel(data=[],
                             message="User deleted successfully.",
                             code=status.HTTP_200_OK)


@router.get("/export/whitelist",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Export a whitelist via csv file")
async def export_whitelist_csv():
    whitelist_data = await retrieve_all_whitelists()
    if isinstance(whitelist_data, Exception):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelists not found."
        )
    for data in whitelist_data:
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
    
    df = pd.DataFrame(whitelist_data)
    df = df.loc[:, ["id", "email", "nickname", "created_at", "updated_at"]]

    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(output,
                             media_type="text/csv",
                             headers={"Content-Disposition": "attachment;filename=whitelist.csv"})

