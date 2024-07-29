from pydantic import BaseModel
from datetime import datetime


class RetakeSchema(BaseModel):
    user_clerk_id: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class RetakeSchemaDB(RetakeSchema):
    exam_id: str


# class UpdateRetake(BaseModel):
#     user_clerk_id: str | None = None
#     exam_id: str | None = None
#     updated_at: datetime = datetime.now()

