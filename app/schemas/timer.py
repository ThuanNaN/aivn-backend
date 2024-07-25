from pydantic import BaseModel

class TimerSchemaDB(BaseModel):
    exam_id: str
    clerk_user_id: str
    start_time: str
