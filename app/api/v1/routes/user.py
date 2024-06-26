from app.utils.logger import Logger
from fastapi import APIRouter, Body, Depends
from app.core.security import is_authenticated
from app.api.v1.controllers.user import (
    add_user,
    retrieve_users,
    retrieve_user,
    retrieve_user_clerk,
    update_user
)
from app.schemas.user import (
    UserSchema,
    UpdateUserSchema,
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
    return ErrorResponseModel(error="An error occurred.",
                              message="User was not retrieved.",
                              code=404)


@router.patch("/user/{clerk_user_id}", description="Update a user with a matching ID")
async def update_user_data(clerk_user_id: str, data: UpdateUserSchema = Body(...)):
    updated = await update_user(clerk_user_id, data.model_dump())
    if updated:
        return ResponseModel(data=[],
                             message="User updated successfully.",
                             code=200)
    return ErrorResponseModel(error="An error occurred.",
                              message="User was not updated.",
                              code=404)


@router.post("/user/upsert", description="Update a user with Clerk data")
async def update_user_via_clerk(clerk_user_id: str = Depends(is_authenticated)):
    clerk_user = await retrieve_user_clerk(clerk_user_id)
    if clerk_user["username"] is None:
        username = clerk_user["first_name"] + " " + clerk_user["last_name"]
    else:
        username = clerk_user["username"]

    if clerk_user["image_url"] is None:
        image_url = "https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.facebook.com%2Faivietnam.edu.vn%2F&psig=AOvVaw1Y_V6Js0AFy7P34aNqjBn3&ust=1719491806171000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCPiK8qOk-YYDFQAAAAAdAAAAABAE"
    else:
        image_url = clerk_user["image_url"]

    role = clerk_user.get("role", "user")

    update_data = UpdateUserSchema(
        username=username,
        role=role,
        avatar=image_url
    )

    is_exist_user = await retrieve_user(clerk_user_id)
    if is_exist_user:
        updated = await update_user(clerk_user_id, update_data.model_dump())
        if updated:
            return ResponseModel(data=[],
                                 message="User updated successfully.",
                                 code=200)
        return ErrorResponseModel(error="An error occurred.",
                                  message="User was not updated.",
                                  code=404)
    else:
        new_user = await add_user(update_data.model_dump())
        return ResponseModel(data=new_user,
                             message="User added successfully.",
                             code=200)
