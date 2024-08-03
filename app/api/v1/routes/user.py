from app.utils.logger import Logger
import csv
from io import StringIO
from fastapi import (
    APIRouter,
    UploadFile, File,
    Body, Depends, status
)
from app.core.security import (
    is_authenticated,
    is_admin
)
from app.api.v1.controllers.user import (
    add_user,
    retrieve_users,
    retrieve_user,
    retrieve_user_clerk,
    update_user,
    add_whitelist,
    retrieve_whitelists,
    check_whitelist_via_email,
    check_whitelist_via_id,
    upsert_whitelist
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
    csv_data = content.decode('utf-8')
    csv_reader = csv.reader(StringIO(csv_data))
    return csv_reader

@router.get("/users",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all users")
async def get_users():
    users = await retrieve_users()
    if isinstance(users, Exception):
        return ErrorResponseModel(error=str(users),
                                  message="An error occurred while retrieving users.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=users,
                             message="Users retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/me", description="Retrieve a user logged in")
async def get_me(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if isinstance(user, Exception):
        return ErrorResponseModel(error=str(user),
                                  message="An error occurred while retrieving user.",
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
        return ErrorResponseModel(error="Whitelists not found.",
                                  message="Cannot find any whitelists.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=whitelists,
                             message="Whitelists retrieved successfully.",
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
        return ErrorResponseModel(error="User not found.",
                                  message="Cannot find user with the provided ID.",
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
        return ErrorResponseModel(error=str(updated),
                                  message="An error occurred while updating user.",
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
            csv_whitelist_data.append(WhiteListSchema(email=row[0], nickname=row[1]))
    whitelist_data = [data.model_dump() for data in csv_whitelist_data]

    whitelist = await add_whitelist(whitelist_data)
    if isinstance(whitelist, Exception):
        return ErrorResponseModel(error=str(whitelist),
                                  message="An error occurred while adding email to whitelist.",
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
            csv_whitelist_data.append(WhiteListSchema(email=row[0], nickname=row[1]))
    whitelist_data = [data.model_dump() for data in csv_whitelist_data]

    updated_whitelist = await upsert_whitelist(whitelist_data)
    if isinstance(updated_whitelist, Exception):
        return ErrorResponseModel(error="An error occurred.",
                                  message="Updating whitelist failed.",
                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return ListResponseModel(data=[],
                             message="Email added to whitelist successfully.",
                             code=status.HTTP_200_OK)


@router.post("/upsert", description="Update a user with Clerk data")
async def update_user_via_clerk(clerk_user_id: str = Depends(is_authenticated)):
    ROLE = "user"  # default role

    # check if user exist in DB
    is_exist_user = await retrieve_user(clerk_user_id)  # -> user_data

    if is_exist_user:  # logged in before
        CURRENT_ROLE = is_exist_user["role"]
        is_whitelist = await check_whitelist_via_id(clerk_user_id)
        if isinstance(is_whitelist, Exception):
            return ErrorResponseModel(error=str(is_whitelist),
                                      message="An error occurred while checking whitelist.",
                                      code=status.HTTP_404_NOT_FOUND)
        if is_whitelist and CURRENT_ROLE != "aio":
            NEW_ROLE = "aio"
            update_role_data = UpdateUserRoleSchema(role=NEW_ROLE)
            updated_role = await update_user(clerk_user_id, update_role_data.model_dump())
            if isinstance(updated_role, Exception):
                return ErrorResponseModel(error=str(updated_role),
                                          message="An error occurred while updating user role.",
                                          code=status.HTTP_404_NOT_FOUND)
            if not updated_role:
                return ErrorResponseModel(error="An error occurred.",
                                          message="User role was not updated.",
                                          code=status.HTTP_404_NOT_FOUND)
            return ListResponseModel(data=[],
                                     message="User updated successfully.",
                                     code=status.HTTP_200_OK)
        return ListResponseModel(data=[],
                                 message="User updated successfully.",
                                 code=status.HTTP_200_OK)

    # first time -> create new user in DB
    else:
        clerk_user_data = await retrieve_user_clerk(clerk_user_id)
        if isinstance(clerk_user_data, Exception):
            return ErrorResponseModel(error=str(clerk_user_data),
                                      message="An error occurred while retrieving user from Clerk.",
                                      code=status.HTTP_404_NOT_FOUND)
        is_whitelist = await check_whitelist_via_email(clerk_user_data["email"])
        if isinstance(is_whitelist, Exception):
            return ErrorResponseModel(error=str(is_whitelist),
                                      message="An error occurred while checking whitelist.",
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
            return ErrorResponseModel(error=str(new_user),
                                      message="An error occurred while adding user.",
                                      code=status.HTTP_404_NOT_FOUND)
        return DictResponseModel(data=new_user,
                                 message="User added successfully.",
                                 code=status.HTTP_200_OK)
