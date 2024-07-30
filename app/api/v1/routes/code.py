from fastapi import APIRouter, status
from app.schemas.code import CodeSchema
from app.schemas.response import (
    DictResponseModel,
    ErrorResponseModel
)
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.run_code import (
    run_testcases
)
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/code", log_file="code.log")


@router.post("/run", description="Run code from code block (string)")
async def run_code(code_inputs: CodeSchema):
    problem_info = await retrieve_problem(code_inputs.problem_id)
    if isinstance(problem_info, Exception):
        return ErrorResponseModel(error=str(problem_info),
                                  message="An error occurred while retrieving problem.",
                                  code=status.HTTP_404_NOT_FOUND)

    admin_template = problem_info.get("admin_template", "")
    public_testcases = problem_info.get("public_testcases", [])
    private_testcases = problem_info.get("private_testcases", [])

    public_results, public_error = await run_testcases(
        admin_template,
        code_inputs.code,
        public_testcases,
        return_testcase=True,
        run_all=True,
        return_details=False
    )

    private_results, private_error = await run_testcases(
        admin_template,
        code_inputs.code,
        private_testcases,
        return_testcase=False
    )

    return DictResponseModel(
        data={
            "public_testcases_results": public_results,
            "private_testcases_results": private_results,
            "error": public_error or private_error or None
        },
        message="Code run successfully.",
        code=status.HTTP_200_OK)
