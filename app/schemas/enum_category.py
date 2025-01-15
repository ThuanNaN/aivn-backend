from enum import Enum

class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def get_list(cls) -> list[str]:
        return [difficulty.value for difficulty in cls]


certificate_map = {
    "foundation": "Math, Programming, and Data Science",
    "basic_deep_learning": "Basic Deep Learning",
    "deep_neural_network": "Deep Neural Networks"
}

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
    
    @classmethod
    def get_certificate_name(cls, certificate_type: str) -> str:
        return certificate_map.get(certificate_type)

