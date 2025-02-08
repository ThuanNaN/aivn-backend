from typing import Optional
from datetime import datetime, UTC
from app.utils import Logger, get_local_year
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
    upsert_admin_list,
    delete_user_by_clerk_user_id
)
from app.api.v1.controllers.whitelist import (
    add_whitelist,
    retrieve_whitelist_by_email,
    delete_whitelist_by_email,
)
from app.schemas.whitelist import (
    WhiteListSchemaDB,
)
from app.schemas.user import (
    UserSchemaDB,
    UpdateUserInfo,
    UpdateUserRole,
    UpdateUserInfoDB,
    UpdateUserRoleDB,
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel
)

router = APIRouter()
logger = Logger("routes/user", log_file="user.log")
ADMIN_COHORT = 2100

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
    search: Optional[str] = Query(None, description="Search by problem title or description"),
    role: Optional[str] = Query(None, description="Filter by role"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    match_stage = {"$match": {}}
    if search:
        match_stage["$match"]["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"role": {"$regex": search, "$options": "i"}},
            {"attend_id": {"$regex": search, "$options": "i"}},
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
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return DictResponseModel(data=user,
                             message="User retrieved successfully.",
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
                                data: UpdateUserInfo = Body(...)):
    data_dict = data.model_dump()
    new_user_data = UpdateUserInfoDB(updated_at=datetime.now(UTC), **data_dict)
    updated = await update_user(clerk_user_id, new_user_data.model_dump())

    if isinstance(updated, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(updated)
        )
    return ListResponseModel(data=[],
                             message="User updated successfully.",
                             code=200)


@router.patch("/{clerk_user_id}",
              dependencies=[Depends(is_admin)],
              tags=["Admin"],
              description="Update a user with a matching ID")
async def update_user_data(clerk_user_id: str, data: UpdateUserRole = Body(...)):
    data_dict = data.model_dump()
    new_role = data_dict.get("role", None)

    user_data = await retrieve_user(clerk_user_id)
    if isinstance(user_data, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Retrieving user data failed."
        )
    current_role = user_data["role"]
    current_cohort = user_data["cohort"]
    current_feasible_cohort = user_data["feasible_cohort"]
    if current_role == new_role:
        return ListResponseModel(data=[],
                                 message="User updated successfully.",
                                 code=200)
    
    if new_role is not None:
        whitelist_info = await retrieve_whitelist_by_email(user_data["email"])
        is_whitelist = True if whitelist_info else False
        if isinstance(is_whitelist, Exception):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Checking whitelist failed."
            )

        if new_role == "aio" and not is_whitelist:
            current_cohort = get_local_year()
            current_feasible_cohort = [current_cohort]
            whitelist_data = WhiteListSchemaDB(
                email=user_data["email"],
                cohort=current_cohort,
                nickname=user_data["username"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            ).model_dump()
            new_whitelist = await add_whitelist(whitelist_data)
            if isinstance(new_whitelist, Exception):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Add whitelist failed."
                )

        if new_role == "user" and is_whitelist:
            current_cohort = 0
            deleted_whitelist = await delete_whitelist_by_email(user_data["email"])
            if isinstance(deleted_whitelist, Exception):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(deleted_whitelist)
                )
            
    update_user_data = UpdateUserRoleDB(
        role=new_role,
        cohort=current_cohort,
        feasible_cohort=current_feasible_cohort,
        updated_at=datetime.now(UTC)
    ).model_dump()
    updated = await update_user(clerk_user_id, update_user_data)
    if isinstance(updated, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(updated)
        )
    return ListResponseModel(data=[],
                             message="User updated successfully.",
                             code=200)



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
    role = "user"  # default role

    # check if user exist in DB
    is_exist_user = await retrieve_user(clerk_user_id)  # -> user_data
    if isinstance(is_exist_user, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(is_exist_user)
        )

    # logged in before -> update role
    if is_exist_user:  
        cur_role = is_exist_user["role"]
        cur_feasible_cohort = is_exist_user["feasible_cohort"]
        if cur_role == "admin":
            current_year = get_local_year()
            ADMIN_FEASIBLE_COHORT = list(range(2022, current_year+1))
            if is_exist_user["cohort"] != ADMIN_COHORT or cur_feasible_cohort != ADMIN_FEASIBLE_COHORT:
                update_cohort_data = UpdateUserRoleDB(
                    role=cur_role,
                    cohort=ADMIN_COHORT,
                    feasible_cohort=ADMIN_FEASIBLE_COHORT,
                    updated_at=datetime.now(UTC)
                ).model_dump()
                updated_cohort = await update_user(clerk_user_id, update_cohort_data)
                if isinstance(updated_cohort, Exception):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=str(updated_cohort)
                    )
            return ListResponseModel(data=[],
                                     message="Upsert user-admin successfully.",
                                     code=status.HTTP_200_OK)
        
        whitelist_info = await retrieve_whitelist_by_email(is_exist_user["email"])
        if isinstance(whitelist_info, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Checking whitelist failed."
            )
        
        # Upsert cohort, is_auditor, role
        if whitelist_info:
            whitelist_cohort = whitelist_info["cohort"]
            is_auditor = whitelist_info["is_auditor"]
            whitelist_feasible_cohort = [whitelist_cohort - 1, whitelist_cohort] if is_auditor else [whitelist_cohort]

            if cur_role == "aio" and whitelist_cohort == is_exist_user["cohort"] and whitelist_feasible_cohort == cur_feasible_cohort:
                return ListResponseModel(data=[],
                                         message="Upsert user-aio successfully.",
                                         code=status.HTTP_200_OK)

            update_role_data = UpdateUserRoleDB(
                role="aio",
                cohort=whitelist_cohort,
                feasible_cohort=whitelist_feasible_cohort,
                updated_at=datetime.now(UTC)
            ).model_dump()
            updated_role = await update_user(clerk_user_id, update_role_data)
            if isinstance(updated_role, Exception):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(updated_role)
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
        cohort = 0
        clerk_user_data = await retrieve_user_clerk(clerk_user_id)
        if isinstance(clerk_user_data, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Retrieving user data failed."
            )
        whitelist_info = await retrieve_whitelist_by_email(clerk_user_data["email"])
        if isinstance(whitelist_info, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Checking whitelist failed."
            )
        if whitelist_info:
            role = "aio"
            cohort = whitelist_info["cohort"]
            if whitelist_info["is_auditor"]:
                feasible_cohort = [cohort - 1, cohort]
            else:
                feasible_cohort = [cohort]
        # Create a new user
        new_user_data = UserSchemaDB(
            clerk_user_id=clerk_user_id,
            email=clerk_user_data["email"],
            username=clerk_user_data["username"],
            role=role,
            cohort=cohort,
            feasible_cohort=feasible_cohort,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(deleted)
        )
    return ListResponseModel(data=[],
                             message="User deleted successfully.",
                             code=status.HTTP_200_OK)