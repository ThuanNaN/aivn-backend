from enum import Enum

class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def get_list(cls) -> list[str]:
        return [difficulty.value for difficulty in cls]
