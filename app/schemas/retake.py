from pydantic import BaseModel
from datetime import datetime, UTC


class RetakeSchema(BaseModel):
    clerk_user_id: str


class RetakeSchemaDB(RetakeSchema):
    creator_id: str
    exam_id: str
    created_at: datetime
