from pydantic import BaseModel
from datetime import datetime


class RetakeSchema(BaseModel):
    user_clerk_id: str
    created_at: datetime = datetime.now()


class RetakeSchemaDB(RetakeSchema):
    exam_id: str
