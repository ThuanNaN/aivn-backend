from pydantic import BaseModel
from datetime import datetime


class RetakeSchema(BaseModel):
    user_clerk_id: str
    created_at: datetime = datetime.now()


class RetakeSchemaDB(RetakeSchema):
    creator_id: str
    exam_id: str
