from pydantic import BaseModel
from datetime import datetime


class RetakeSchema(BaseModel):
    clerk_user_id: str
    created_at: datetime = datetime.now()


class RetakeSchemaDB(RetakeSchema):
    creator_id: str
    exam_id: str
