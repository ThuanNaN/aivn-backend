from app.utils.logger import Logger
from fastapi import APIRouter, Body, Depends
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
    check_whitelist_via_id
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


@router.get("/users",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all users")
async def get_users():
    users = await retrieve_users()
    if users:
        return ListResponseModel(data=users,
                                 message="Users retrieved successfully.",
                                 code=200)
    return ListResponseModel(data=[],
                             message="No users exist.",
                             code=404)


@router.get("/me", description="Retrieve a user logged in")
async def get_me(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if user:
        return DictResponseModel(data=user,
                                 message="User retrieved successfully.",
                                 code=200)
    return ErrorResponseModel(error="An error occurred.",
                              message="User was not retrieved.",
                              code=404)


@router.get("/{clerk_user_id}",
            description="Retrieve a user with a matching ID")
async def get_user(clerk_user_id: str):
    user = await retrieve_user(clerk_user_id)
    if user:
        return DictResponseModel(data=user,
                                 message="User retrieved successfully.",
                                 code=200)
    return ErrorResponseModel(error="An error occurred when get user by id",
                              message="User was not retrieved.",
                              code=404)


@router.patch("/{clerk_user_id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a user with a matching ID")
async def update_user_data(clerk_user_id: str, data: UpdateUserSchema = Body(...)):
    updated = await update_user(clerk_user_id, data.model_dump())
    if updated:
        return ListResponseModel(data=[],
                                 message="User updated successfully.",
                                 code=200)
    return ErrorResponseModel(error="An error occurred.",
                              message="User was not updated.",
                              code=404)


@router.post("/whitelist",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add an email to whitelist")
async def add_email_to_whitelist(whitelist_data: WhiteListSchema):
    whitelist = await add_whitelist(whitelist_data.model_dump())
    return whitelist


@router.get("/whitelists",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all whitelists")
async def get_whitelists():
    whitelists = await retrieve_whitelists()
    if whitelists:
        return ListResponseModel(data=whitelists,
                                 message="Whitelists retrieved successfully.",
                                 code=200)
    return ListResponseModel(data=[],
                             message="No whitelists exist.",
                             code=404)


@router.post("/upsert", description="Update a user with Clerk data")
async def update_user_via_clerk(clerk_user_id: str = Depends(is_authenticated)):
    ROLE = "user"  # default role

    # check if user exist in DB
    is_exist_user = await retrieve_user(clerk_user_id)  # -> user_data

    if is_exist_user:  # logged in before
        CURRENT_ROLE = is_exist_user["role"]
        is_whitelist = await check_whitelist_via_id(clerk_user_id)
        if is_whitelist and CURRENT_ROLE != "aio":
            NEW_ROLE = "aio"
            update_role_data = UpdateUserRoleSchema(role=NEW_ROLE)
            updated_role = await update_user(clerk_user_id, update_role_data.model_dump())
            if updated_role:
                return ListResponseModel(data=[],
                                         message="User updated successfully.",
                                         code=200)
            return ErrorResponseModel(error="An error occurred.",
                                      message="User role was not updated.",
                                      code=404)

        return ListResponseModel(data=[],
                                 message="User updated successfully.",
                                 code=200)

        # no update role
        # just update username and avatar

        # clerk_user_data = await retrieve_user_clerk(clerk_user_id)
        # if not clerk_user_data:
        #     return ErrorResponseModel(error="An error occurred.",
        #                               message="User was not retrieved from Clerk.",
        #                               code=404)
        # update_info_data = UpdateUserInfoSchema(
        #     username=clerk_user_data["username"],
        #     avatar=clerk_user_data["avatar"])

        # updated_info_data = await update_user(clerk_user_id, update_info_data.model_dump())
        # if updated_info_data:
        #     return ResponseModel(data=[],
        #                          message="User updated successfully.",
        #                          code=200)
        # return ErrorResponseModel(error="An error occurred.",
        #                           message="User info was not updated.",
        #                           code=404)

    # first time -> create new user in DB
    else:
        clerk_user_data = await retrieve_user_clerk(clerk_user_id)
        if not clerk_user_data:
            return ErrorResponseModel(error="An error occurred.",
                                      message="User was not retrieved from Clerk.",
                                      code=404)
        is_whitelist = await check_whitelist_via_email(clerk_user_data["email"])
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
        if new_user:
            return DictResponseModel(data=new_user,
                                     message="User added successfully.",
                                     code=200)
        return ErrorResponseModel(error="An error occurred.",
                                  message="User was not added.",
                                  code=404)
