from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from .category import CategoryModel
from .difficulty import DifficultyEnum


class TestCase(BaseModel):
    testcase_id: UUID = Field(default_factory=uuid4)
    init_kwargs: str | None = None
    input_kwargs: str | None = None
    expected_output: str | None = None


class Choice(BaseModel):
    choice_id: UUID = Field(default_factory=uuid4)
    answer: str | None = None
    is_correct: bool | None = None


class ProblemSchema(BaseModel):
    title: str
    description: str
    slug: str
    difficulty: str | None = DifficultyEnum.EASY.value
    categories: List[CategoryModel] | None = [CategoryModel(category_id=uuid4(),
                                                            category_name="python")]

    # >>> code problems
    admin_template: str | None = None
    code_template: str | None
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
                    "categories": [CategoryModel(category_id=uuid4(),
                                                category_name="python").model_dump()],
                    "admin_template": "import numpy as np",
                    "code_template": "def add(a, b):\n    return a + b",
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


class ProblemSchemaDB(ProblemSchema):
    creator_id: str


class UpdateProblemSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    slug: str | None = None
    difficulty: DifficultyEnum = DifficultyEnum.EASY.value
    categories: CategoryModel = CategoryModel(category_id=uuid4(),
                                              category_name=CategoryEnum.PYTHON.value)
    admin_template: str | None = None
    code_template: str | None = None
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
                    "categories": [CategoryModel(category_id=uuid4(),
                                                category_name=CategoryEnum.PYTHON.value).model_dump()],
                    "admin_template": "import numpy as np",
                    "code_template": "def add(a, b):\n    return a + b",
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

class UpdateProblemSchemaDB(UpdateProblemSchema):
    creator_id: str