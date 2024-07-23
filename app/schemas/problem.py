from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from .difficulty import DifficultyEnum


class TestCase(BaseModel):
    testcase_id: UUID = Field(default_factory=uuid4)
    init_kwargs: str | None = None
    input_kwargs: str | None = None
    expected_output: str


class Choice(BaseModel):
    choice_id: UUID = Field(default_factory=uuid4)
    answer: str
    is_correct: bool


class ProblemSchema(BaseModel):
    title: str
    description: str
    slug: str
    difficulty: str | None = DifficultyEnum.EASY.value
    category_ids: List[str] = []
    is_published: bool = True

    # >>> code problems
    admin_template: str
    code_template: str
    code_solution: str
    public_testcases: List[TestCase] | None = None
    private_testcases:  List[TestCase] | None = None
    # >>> code problems

    # >>> choice problems
    choices: List[Choice] | None = None
    # >>> choice problems

    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Add two numbers",
                    "description": "Add two numbers and return the sum",
                    "slug": "add-two-numbers",
                    "difficulty": DifficultyEnum.EASY.value,
                    "category_ids": ["6699cd66a68124e8119e909f"],
                    "is_published": False,
                    "admin_template": "import numpy as np",
                    "code_template": "def add(a, b):\n    # Code here",
                    "code_solution": "def add(a, b):\n    return a + b",
                    "public_testcases": [
                        {
                            "testcase_id": uuid4(),
                            "init_kwargs": "a=1\nb=2",
                            "input_kwargs": "",
                            "expected_output": "3"
                        }
                    ],
                    "private_testcases": [
                        {
                            "testcase_id": uuid4(),
                            "init_kwargs": "a=2\nb=2",
                            "input_kwargs": "",
                            "expected_output": "4"
                        }
                    ],
                    "choices": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
        }
    }


class ProblemSchemaDB(BaseModel):
    creator_id: str
    title: str
    description: str
    slug: str
    difficulty: str | None = DifficultyEnum.EASY.value
    is_published: bool = True

    # >>> code problems
    admin_template: str 
    code_template: str 
    code_solution: str 
    public_testcases: List[TestCase] | None = None
    private_testcases:  List[TestCase] | None = None
    # >>> code problems

    # >>> choice problems
    choices: List[Choice] | None = None
    # >>> choice problems

    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class UpdateProblemSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    slug: str | None = None
    difficulty: str | None = DifficultyEnum.EASY.value
    category_ids: List[str] | None = None
    admin_template: str | None = None
    code_template: str | None = None
    code_solution: str | None = None
    public_testcases: List[TestCase] | None = None
    private_testcases: List[TestCase] | None = None
    choices: List[Choice] | None = None
    updated_at: datetime = datetime.now()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Add two numbers",
                    "description": "Add two numbers and return the sum",
                    "slug": "add-two-numbers",
                    "difficulty": DifficultyEnum.EASY,
                    "category_ids": ["6699cd6da68124e8119e90a0"],
                    "is_published": False,
                    "admin_template": "import numpy as np",
                    "code_template": "def add(a, b):\n    # Code here",
                    "code_solution": "def add(a, b):\n    return a + b",
                    "public_testcases": [
                        {
                            "testcase_id": uuid4(),
                            "init_kwargs": "a=1\nb=2",
                            "input_kwargs": "",
                            "expected_output": "3"
                        }
                    ],
                    "private_testcases": [
                        {
                            "testcase_id": uuid4(),
                            "init_kwargs": "a=2\nb=2",
                            "input_kwargs": "",
                            "expected_output": "4"
                        }
                    ],
                    "choices": None,
                    "updated_at": datetime.now()
                }
            ]
        }
    }

class UpdateProblemSchemaDB(BaseModel):
    creator_id: str
    title: str | None = None
    description: str | None = None
    slug: str | None = None
    difficulty: str | None = DifficultyEnum.EASY.value
    admin_template: str | None = None
    code_template: str | None = None
    code_solution: str | None = None
    public_testcases: List[TestCase] | None = None
    private_testcases: List[TestCase] | None = None
    choices: List[Choice] | None = None
    updated_at: datetime = datetime.now()