from fastapi import APIRouter, status
from app.schemas.code import CodeSchema, ResponseModel, ErrorResponseModel
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.run_code import test_py_funct
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/code", log_file="code.log")


@router.post("/run", description="Run code from code block (string)")
async def run_code(code_inputs: CodeSchema):
    problem_info = await retrieve_problem(code_inputs.problem_id)
    if not problem_info:
        logger.error(f"Problem with ID {code_inputs.problem_id} not found.")
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problem not found.",
                                  code=status.HTTP_404_NOT_FOUND)

    admin_template = problem_info.get("admin_template", "")
    public_testcases = problem_info.get("public_testcases", [])
    private_testcases = problem_info.get("private_testcases", [])

    async def run_testcases(admin_template: str, code: str, testcases, return_testcase):
        if not testcases:
            return [], None
        results_dict = await test_py_funct(admin_template=admin_template,
                                           py_func=code,
                                           testcases=testcases,
                                           return_testcase=return_testcase,
                                           run_all=True)
        result = results_dict["testcase_outputs"]
        error = results_dict["error"]
        return result, error

    public_results, public_error = await run_testcases(admin_template,
                                                       code_inputs.code,
                                                       public_testcases,
                                                       True)

    private_results, private_error = await run_testcases(admin_template,
                                                         code_inputs.code,
                                                         private_testcases,
                                                         False)

    return ResponseModel(
        data={
            "public_testcases_results": public_results,
            "private_testcases_results": private_results,
            "error": public_error or private_error or None
        },
        message="Code run successfully.",
        code=status.HTTP_200_OK)
