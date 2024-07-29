from typing import List
from pydantic import BaseModel


class ListResponseModel(BaseModel):
    data: List[list] | List[dict] | list
    message: str
    code: int


class DictResponseModel(BaseModel):
    data: dict
    message: str
    code: int


class ErrorResponseModel(BaseModel):
    error: str
    message: str
    code: int