from pydantic import BaseModel

class TimerSchema(BaseModel):
    start_time: str


class TimerSchemaDB(TimerSchema):
    exam_id: str
    clerk_user_id: str
