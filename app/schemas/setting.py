from pydantic import BaseModel

class SettingSchema(BaseModel):
    duration: int

class ResponseModel(BaseModel):
    data: dict
    message: str
    code: int

class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int