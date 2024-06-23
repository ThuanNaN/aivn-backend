from fastapi import APIRouter, Body
from app.schemas.code import CodeSchema, ResponseModel, ErrorResponseModel
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.run_code import test_py_funct
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/code", log_file="code.log")


@router.post("/run", description="Run code from code block (string)")
async def run_code(code_inputs: CodeSchema = Body(...)):
    problem = await retrieve_problem(code_inputs.problem_id)
    if not problem:
        logger.error(f"Problem with ID {code_inputs.problem_id} not found.")
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problem not found.",
                                  code=404)

    public_testcases = problem["public_testcases"]
    private_testcases = problem["private_testcases"]

    # Run code
    public_testcases_results = test_py_funct(code_inputs.code, 
                                             public_testcases, 
                                             return_testcase=True)
    
    private_testcases_results = test_py_funct(code_inputs.code, 
                                              private_testcases)

    return ResponseModel(
        data={
            "public_testcases_results": public_testcases_results,
            "private_testcases_results": private_testcases_results,
        },
        message="Code run successfully.",
        code=200)
