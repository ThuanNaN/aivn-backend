from pydantic import BaseModel
from datetime import datetime


class TimerSchemaDB(BaseModel):
    exam_id: str
    clerk_user_id: str
    start_time: datetime = datetime.now()
