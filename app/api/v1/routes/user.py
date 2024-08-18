from typing import Optional
from app.utils.logger import Logger
import csv
from io import StringIO
from fastapi import (
    APIRouter,
    UploadFile, File, Query,
    Body, Depends, status
)
from app.core.security import (
    is_authenticated,
    is_admin
)
from app.api.v1.controllers.user import (
    add_user,
    retrieve_users,
    retrieve_user_by_pipeline,
    retrieve_user,
    retrieve_user_by_email,
    retrieve_admin_users,
    retrieve_user_clerk,
    update_user,
    add_whitelist,
    retrieve_whitelists,
    check_whitelist_via_email,
    check_whitelist_via_id,
    upsert_whitelist,
    upsert_admin_list
)
from app.schemas.user import (
    UserSchema,
    UpdateUserSchema,
    UpdateUserRoleSchema,
    WhiteListSchema,
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)

router = APIRouter()
logger = Logger("routes/user", log_file="user.log")


async def read_csv(file: UploadFile):
    content = await file.read()
    csv_data = content.decode('utf-8-sig')
    csv_reader = csv.reader(StringIO(csv_data))
    return csv_reader

@router.get("/users",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all users with matching search and filter")
async def get_users(
    search: Optional[str] = Query(
        None,
        description="Search by problem title or description"),
    role: Optional[str] = Query(
        None,
        description="Filter by role"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"role": {"$regex": search, "$options": "i"}},
        ]

    if role is not None:
        match_stage["$match"]["role"] = role

    pipeline = [
        match_stage,
        {
            "$facet": {
                "users": [
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
    users = await retrieve_user_by_pipeline(pipeline, page, per_page)
    if isinstance(users, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving users failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=users,
                             message="Users retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/me", description="Retrieve a user logged in")
async def get_me(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving user failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/whitelists",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve whitelist users")
async def get_whitelists():
    whitelists = await retrieve_whitelists()
    if isinstance(whitelists, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving whitelists failed.",
                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not whitelists:
        return ErrorResponseModel(error="An error occurred.",
                                  message="Whitelists not found.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=whitelists,
                             message="Whitelists retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/admins",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all admin users")
async def get_admin_users():
    users = await retrieve_admin_users()
    if isinstance(users, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving admin users failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not users:
        return ErrorResponseModel(error="An error occurred.",
                                  message="Admin users not found.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=users,
                             message="Admin users retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/email/{email}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Check if email is in whitelist")
async def get_user_by_email(email: str):
    user = await retrieve_user_by_email(email)
    if isinstance(user, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving user failed.",
                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not user:
        return ErrorResponseModel(error="An error occurred.",
                                  message="User not found.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{clerk_user_id}",
            description="Retrieve a user with a matching ID")
async def get_user(clerk_user_id: str):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Retrieving user failed.",
                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not user:
        return ErrorResponseModel(error="An error occurred.",
                                  message="User not found.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.patch("/{clerk_user_id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a user with a matching ID")
async def update_user_data(clerk_user_id: str, data: UpdateUserSchema = Body(...)):
    updated = await update_user(clerk_user_id, data.model_dump())
    if isinstance(updated, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Updating user failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not updated:
        return ErrorResponseModel(error="An error occurred.",
                                  message="User was not updated.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=[],
                             message="User updated successfully.",
                             code=200)


@router.post("/whitelist",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add an email to whitelist")
async def add_email_to_whitelist(whitelist_csv: UploadFile = File(...)):
    csv_reader = await read_csv(whitelist_csv)
    csv_whitelist_data = []
    for row in csv_reader:
        if len(row) >= 2:
            csv_whitelist_data.append(WhiteListSchema(email=row[0].lower(), nickname=row[1]))
    whitelist_data = [data.model_dump() for data in csv_whitelist_data]

    whitelist = await add_whitelist(whitelist_data)
    if isinstance(whitelist, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Adding email to whitelist failed.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=whitelist,
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)


@router.post("/whitelist/upsert",
                dependencies=[Depends(is_admin)],
                tags=["Admin"],
                description="Upsert whitelist collection")
async def upsert_whitelist_data(whitelist_csv: UploadFile = File(...)):
    csv_reader = await read_csv(whitelist_csv)
    csv_whitelist_data = []
    for row in csv_reader:
        if len(row) >= 2:
            csv_whitelist_data.append(WhiteListSchema(email=row[0].lower(), nickname=row[1]))
    whitelist_data = [data.model_dump() for data in csv_whitelist_data]

    updated_whitelist = await upsert_whitelist(whitelist_data)
    if isinstance(updated_whitelist, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Updating whitelist failed.",
                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return ListResponseModel(data=[],
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)



@router.post("/admin/upsert", 
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Update a user role to admin")
async def update_user_role_to_admin(admin_csv: UploadFile = File(...)):
    csv_reader = await read_csv(admin_csv)
    admin_info = []
    for row in csv_reader:
        if len(row) >= 2:
            admin_info.append({
                "email": row[0],
                # "nickname": row[1]
            })
    updated_admin = await upsert_admin_list(admin_info)
    if isinstance(updated_admin, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Updating admin list failed.",
                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not updated_admin:
        return ErrorResponseModel(error="An error occurred.",
                                  message="User role was not updated.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=[],
                             message="User role updated to admin successfully.",
                             code=status.HTTP_200_OK)



@router.post("/upsert", description="Update a user with Clerk data")
async def update_user_via_clerk(clerk_user_id: str = Depends(is_authenticated)):
    ROLE = "user"  # default role

    # check if user exist in DB
    is_exist_user = await retrieve_user(clerk_user_id)  # -> user_data

    if is_exist_user:  # logged in before
        CURRENT_ROLE = is_exist_user["role"]
        if CURRENT_ROLE == "admin":
            return ListResponseModel(data=[],
                                     message="Current user is an admin.",
                                     code=status.HTTP_200_OK)

        is_whitelist = await check_whitelist_via_id(clerk_user_id)
        if isinstance(is_whitelist, Exception):
            return ErrorResponseModel(error="An error occurred.",
                                      message="Checking whitelist failed.",
                                      code=status.HTTP_404_NOT_FOUND)
        if is_whitelist and CURRENT_ROLE != "aio":
            NEW_ROLE = "aio"
            update_role_data = UpdateUserRoleSchema(role=NEW_ROLE)
            updated_role = await update_user(clerk_user_id, update_role_data.model_dump())
            if isinstance(updated_role, Exception):
                return ErrorResponseModel(error="An error occurred.",
                                          message="Updating user role failed.",
                                          code=status.HTTP_404_NOT_FOUND)
            if not updated_role:
                return ErrorResponseModel(error="An error occurred.",
                                          message="User role was not updated.",
                                          code=status.HTTP_404_NOT_FOUND)
            return ListResponseModel(data=[],
                                     message="User updated successfully.",
                                     code=status.HTTP_200_OK)
        else:
            return ListResponseModel(data=[],
                                    message="Upsert user successfully.",
                                    code=status.HTTP_200_OK)

    # first time -> create new user in DB
    else:
        clerk_user_data = await retrieve_user_clerk(clerk_user_id)
        if isinstance(clerk_user_data, Exception):
            return ErrorResponseModel(error="An error occurred.",
                                      message="Retrieving user data failed.",
                                      code=status.HTTP_404_NOT_FOUND)
        is_whitelist = await check_whitelist_via_email(clerk_user_data["email"])
        if isinstance(is_whitelist, Exception):
            return ErrorResponseModel(error="An error occurred.",
                                      message="Checking whitelist failed.",
                                      code=status.HTTP_404_NOT_FOUND)
        if is_whitelist:
            ROLE = "aio"
        # Create a new user
        new_user_data = UserSchema(
            clerk_user_id=clerk_user_id,
            email=clerk_user_data["email"],
            username=clerk_user_data["username"],
            role=ROLE,
            avatar=clerk_user_data["avatar"]
        )
        new_user = await add_user(new_user_data.model_dump())
        if isinstance(new_user, Exception):
            return ErrorResponseModel(error="An error occurred.",
                                      message="Adding user failed.",
                                      code=status.HTTP_404_NOT_FOUND)
        return DictResponseModel(data=new_user,
                                 message="User added successfully.",
                                 code=status.HTTP_200_OK)
