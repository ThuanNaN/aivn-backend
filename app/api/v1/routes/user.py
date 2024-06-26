from app.utils.logger import Logger
from fastapi import APIRouter, Body, Depends
from app.core.security import is_authenticated
from app.api.v1.controllers.user import (
    add_user,
    retrieve_users,
    retrieve_user,
    retrieve_user_clerk,
    update_user,
    add_whitelist,
    retrieve_whitelists,
    check_whitelist
)
from app.schemas.user import (
    UserSchema,
    UpdateUserInfoSchema,
    UpdateUserRoleSchema,
    WhiteListSchema,
    ResponseModel,
    ErrorResponseModel,
)

router = APIRouter()
logger = Logger("routes/user", log_file="user.log")


@router.post("/user", description="Add a new user")
async def create_user(user: UserSchema):
    user_dict = user.model_dump()
    new_user = await add_user(user_dict)
    return new_user


@router.get("/users", description="Retrieve all users")
async def get_users():
    users = await retrieve_users()
    if users:
        return ResponseModel(data=users,
                             message="Users retrieved successfully.",
                             code=200)
    return ResponseModel(data=[],
                         message="No users exist.",
                         code=404)


@router.get("/user/{clerk_user_id}", description="Retrieve a user with a matching ID")
async def get_user(clerk_user_id: str):
    user = await retrieve_user(clerk_user_id)
    if user:
        return ResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=200)
    return ErrorResponseModel(error="An error occurred when get user by id",
                              message="User was not retrieved.",
                              code=404)


@router.patch("/user/{clerk_user_id}", description="Update a user with a matching ID")
async def update_user_data(clerk_user_id: str, data: UpdateUserInfoSchema = Body(...)):
    updated = await update_user(clerk_user_id, data.model_dump())
    if updated:
        return ResponseModel(data=[],
                             message="User updated successfully.",
                             code=200)
    return ErrorResponseModel(error="An error occurred.",
                              message="User was not updated.",
                              code=404)


@router.get("/me", description="Retrieve a user logged in")
async def get_me(clerk_user_id: str = Depends(is_authenticated)):
    user = await retrieve_user(clerk_user_id)
    if user:
        return ResponseModel(data=user,
                             message="User retrieved successfully.",
                             code=200)
    return ErrorResponseModel(error="An error occurred.",
                              message="User was not retrieved.",
                              code=404)


@router.post("/whitelist", description="Add an email to whitelist")
async def add_email_to_whitelist(whitelist_data: WhiteListSchema):
    whitelist = await add_whitelist(whitelist_data.model_dump())
    return whitelist


@router.get("/whitelists", description="Retrieve all whitelists")
async def get_whitelists():
    whitelists = await retrieve_whitelists()
    if whitelists:
        return ResponseModel(data=whitelists,
                             message="Whitelists retrieved successfully.",
                             code=200)
    return ResponseModel(data=[],
                         message="No whitelists exist.",
                         code=404)


@router.post("/upsert", description="Update a user with Clerk data")
async def update_user_via_clerk(clerk_user_id: str = Depends(is_authenticated)):
    clerk_user_data = await retrieve_user_clerk(clerk_user_id)

    is_exist_user = await retrieve_user(clerk_user_id)
    if not clerk_user_data:
        return ErrorResponseModel(error="An error occurred.",
                                  message="User was not retrieved from Clerk.",
                                  code=404)
    
    role = "user" # default role
    is_whitelist = await check_whitelist(clerk_user_data["email"])

    if is_exist_user: # logged before
        if is_whitelist:
            # Update role to aio
            role = "aio"
            update_data = UpdateUserRoleSchema(
                username=clerk_user_data["username"],
                avatar=clerk_user_data["avatar"],
                role=role)
        else: # -> [user, admin]
            update_data = UpdateUserInfoSchema(
                username=clerk_user_data["username"],
                avatar=clerk_user_data["avatar"])

        updated = await update_user(clerk_user_id, update_data.model_dump())
        if updated:
            return ResponseModel(data=[],
                                 message="User updated successfully.",
                                 code=200)
        return ErrorResponseModel(error="An error occurred.",
                                  message="User was not updated.",
                                  code=404)
    else:
        if is_whitelist:
            role = "aio"
        # Create a new user
        new_user_data = UserSchema(
            clerk_user_id=clerk_user_id,
            email=clerk_user_data["email"],
            username=clerk_user_data["username"],
            role=role,
            avatar=clerk_user_data["avatar"]
        )
        new_user = await add_user(new_user_data.model_dump())
        return ResponseModel(data=new_user,
                             message="User added successfully.",
                             code=200)