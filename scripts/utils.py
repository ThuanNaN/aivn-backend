from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from enum import Enum

class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def get_list(cls) -> list[str]:
        return [difficulty.value for difficulty in cls]

class CategoryEnum(Enum):
    PYTHON = "6699cd66a68124e8119e909f"
    PYTORCH = "6699cd6da68124e8119e90a0"
    NUMPY = "669e011158e05c2a19651a85"

    @classmethod
    def get_list(cls) -> list[str]:
        return [category.value for category in cls]


class TestCase(BaseModel):
    testcase_id: UUID = Field(default_factory=uuid4)
    init_kwargs: str | None = None
    input_kwargs: str | None = None
    expected_output: str | None = None


class Choice(BaseModel):
    choice_id: UUID = Field(default_factory=uuid4)
    answer: str | None = None
    is_correct: bool | None = None