from typing import Optional
from datetime import datetime, UTC
from app.utils.logger import Logger
import csv
from io import StringIO
from fastapi import (
    APIRouter,
    UploadFile, 
    File, Query, Body, Depends, 
    HTTPException, status
)
from app.core.security import (
    is_authenticated,
    is_admin
)
from app.api.v1.controllers.user import (
    add_user,
    retrieve_user_by_pipeline,
    retrieve_user,
    retrieve_user_by_email,
    retrieve_admin_users,
    retrieve_user_clerk,
    update_user,
    add_whitelist,
    add_whitelist_via_file,
    retrieve_whitelists,
    check_whitelist_via_email,
    check_whitelist_via_id,
    upsert_whitelist,
    upsert_admin_list,
    delete_whitelist_by_email,
    delete_user_by_clerk_user_id
)
from app.schemas.user import (
    UserSchemaDB,
    UpdateUserSchema,
    UpdateUserSchemaDB,
    WhiteListSchema,
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    return DictResponseModel(data=users,
                             message="Users retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/me", description="Retrieve a user logged in")
async def get_me(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get whitelists failed."
        )
    if not whitelists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelists not found."
        )
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get admin list failed."
        )
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admins not found."
        )
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get user failed."
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return DictResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{clerk_user_id}",
            description="Retrieve a user with a matching ID")
async def get_user(clerk_user_id: str):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get user failed."
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return DictResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.patch("/me/update",
              description="Update a user with Clerk data")
async def update_user_via_clerk(clerk_user_id: str = Depends(is_authenticated), 
                                data: UpdateUserSchema = Body(...)):
    data_dict = data.model_dump()

    current_user = await retrieve_user(clerk_user_id)
    current_user_role = current_user["role"]

    if current_user_role != "admin":
        data_dict.pop("role")

    new_user_data = UpdateUserSchemaDB(updated_at=datetime.now(UTC), **data_dict)
    updated = await update_user(clerk_user_id, new_user_data.model_dump())

    if isinstance(updated, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not updated."
        )
    return ListResponseModel(data=[],
                             message="User updated successfully.",
                             code=200)


@router.patch("/{clerk_user_id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a user with a matching ID")
async def update_user_data(clerk_user_id: str, data: UpdateUserSchema = Body(...)):
    data_dict = data.model_dump()
    new_role = data_dict.get("role", None)
    if new_role is not None:
        user_data = await retrieve_user(clerk_user_id)
        is_whitelist = await check_whitelist_via_email(user_data["email"])
        if isinstance(is_whitelist, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Checking whitelist failed."
            )

        if new_role == "aio" and not is_whitelist:
            whitelist_data = WhiteListSchema(
                email=user_data["email"],
                nickname=user_data["username"]
            ).model_dump()
            new_whitelist = await add_whitelist(whitelist_data)
            if isinstance(new_whitelist, Exception):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Add whitelist failed."
                )

        if new_role == "user" and is_whitelist:
            deleted_whitelist = await delete_whitelist_by_email(user_data["email"])
            if isinstance(deleted_whitelist, Exception):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred."
                )
            if not deleted_whitelist:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deleting email from whitelist failed."
                )
    new_user_data = UpdateUserSchemaDB(updated_at=datetime.now(UTC), **data_dict)
    updated = await update_user(clerk_user_id, new_user_data.model_dump())
    if isinstance(updated, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not updated."
        )
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

    whitelist = await add_whitelist_via_file(whitelist_data)
    if isinstance(whitelist, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    return DictResponseModel(data=whitelist,
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)


@router.post("/whitelist/upsert",
                dependencies=[Depends(is_admin)],
                tags=["Admin"],
                description="This API will upsert the whitelist data, \
                            if the email is already in the whitelist FILE, it will be UPDATED. \
                            Otherwise, if the email is not EXIST, it will be ADDED. \
                            In case of the email is EXIST in database, but not in the whitelist FILE, It will be DELETED.")
async def upsert_whitelist_data(whitelist_csv: UploadFile = File(...)):
    csv_reader = await read_csv(whitelist_csv)
    csv_whitelist_data = []
    for row in csv_reader:
        if len(row) >= 2:
            csv_whitelist_data.append(WhiteListSchema(email=row[0].lower(), nickname=row[1]))
    whitelist_data = [data.model_dump() for data in csv_whitelist_data]

    updated_whitelist = await upsert_whitelist(whitelist_data)
    if isinstance(updated_whitelist, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    return ListResponseModel(data=[],
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)



@router.post("/admin/upsert", 
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="This API is used to update the user in role 'user', 'aio', or 'admin' to admin role.\
                          If the current admin not in the Admin FILE, it will be down role to 'aio'.")
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred."
        )
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update admin list failed."
        )
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Checking whitelist failed."
            )
        if is_whitelist and CURRENT_ROLE != "aio":
            NEW_ROLE = "aio"
            update_role_data = UpdateUserSchemaDB(role=NEW_ROLE, 
                                                  updated_at=datetime.now(UTC))
            updated_role = await update_user(clerk_user_id, update_role_data.model_dump())
            if isinstance(updated_role, Exception):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred."
                )
            if not updated_role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Updating user role failed."
                )
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Retrieving user data failed."
            )
        is_whitelist = await check_whitelist_via_email(clerk_user_data["email"])
        if isinstance(is_whitelist, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Checking whitelist failed."
            )
        if is_whitelist:
            ROLE = "aio"
        # Create a new user
        new_user_data = UserSchemaDB(
            clerk_user_id=clerk_user_id,
            email=clerk_user_data["email"],
            username=clerk_user_data["username"],
            role=ROLE,
            avatar=clerk_user_data["avatar"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        new_user = await add_user(new_user_data.model_dump())
        if isinstance(new_user, Exception):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adding user failed."
            )
        return DictResponseModel(data=new_user,
                                 message="User added successfully.",
                                 code=status.HTTP_200_OK)


@router.delete("/{clerk_user_id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a user with a matching clerk_user_id")
async def delete_user(clerk_user_id: str):
    deleted = await delete_user_by_clerk_user_id(clerk_user_id)
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