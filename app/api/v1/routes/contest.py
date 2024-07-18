from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.api.v1.controllers.contest import (
    add_contest,
    retrieve_contests,
    retrieve_contest,
    update_contest,
    delete_contest
)
from app.schemas.contest import (
    ContestSchema,
    UpdateContestSchema,
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated

router = APIRouter()
logger = Logger("routes/contest", log_file="contest.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Create a new contest")
async def create_contest(contest: ContestSchema):
    contest_dict = contest.model_dump()
    new_contest = await add_contest(contest_dict)
    return DictResponseModel(data=new_contest,
                             message="Contest created successfully.",
                             code=status.HTTP_200_OK)


@router.get("/contests",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all contests")
async def get_contests():
    contests = await retrieve_contests()
    if contests:
        return ListResponseModel(data=contests,
                                 message="Contests retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when retrieve contests.",
                              message="Contests not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a contest with a matching ID")
async def get_contest(id: str):
    contest = await retrieve_contest(id)
    if contest:
        return DictResponseModel(data=contest,
                                 message="Contest retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when retrieve contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a contest with a matching ID")
async def update_contest_data(id: str, contest: UpdateContestSchema):
    contest_dict = contest.model_dump()
    updated = await update_contest(id, contest_dict)
    if updated:
        return ListResponseModel(data=[],
                                 message="Contest updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when update contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a contest with a matching ID")
async def delete_contest_data(id: str):
    deleted = await delete_contest(id)
    if deleted:
        return ListResponseModel(data=[],
                                 message="Contest deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when delete contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)
