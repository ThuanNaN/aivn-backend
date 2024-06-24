from fastapi import APIRouter, Body
from app.schemas.code import CodeSchema, ResponseModel, ErrorResponseModel
from app.api.v1.controllers.problem import retrieve_problem
from app.api.v1.controllers.run_code import test_py_funct
from app.utils.logger import Logger

router = APIRouter()
logger = Logger("routes/code", log_file="code.log")


@router.post("/run", description="Run code from code block (string)")
async def run_code(code_inputs: CodeSchema):
    problem = await retrieve_problem(code_inputs.problem_id)
    if not problem:
        logger.error(f"Problem with ID {code_inputs.problem_id} not found.")
        return ErrorResponseModel(error="An error occurred.",
                                  message="Problem not found.",
                                  code=404)

    public_testcases = problem.get("public_testcases", [])
    private_testcases = problem.get("private_testcases", [])

    def run_testcases(code, testcases, return_testcase):
        if not testcases:
            return []
        results_dict = test_py_funct(py_func=code, 
                                     testcases=testcases, 
                                     return_testcase=return_testcase)
        
        logger.info(f'Error: {results_dict["error"]}')
        if results_dict["error"] is not None:
            return ErrorResponseModel(
                error="Error running code.",
                message=results_dict["error"],
                code=500
            )
        return results_dict["testcase_outputs"]

    public_results = run_testcases(code_inputs.code, public_testcases, True)
    if isinstance(public_results, ErrorResponseModel):
        return public_results

    private_results = run_testcases(code_inputs.code, private_testcases, False)
    if isinstance(private_results, ErrorResponseModel):
        return private_results
    

    logger.info(f"public_results: {public_results}" )

    return ResponseModel(
        data={
            "public_testcases_results": public_results,
            "private_testcases_results": [],
        },
        message="Code run successfully.",
        code=200)
