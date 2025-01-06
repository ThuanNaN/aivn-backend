from enum import Enum

class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def get_list(cls) -> list[str]:
        return [difficulty.value for difficulty in cls]

class CertificateEnum(Enum):
    """
    Enum class for Certificate Template
    """

    FOUNDATION = "foundation"
    BASIC_DL = "basic_deep_learning"
    DEEP_NN = "deep_neural_network"

    @classmethod
    def get_list(cls) -> list[str]:
        return [certificate_type.value for certificate_type in cls]