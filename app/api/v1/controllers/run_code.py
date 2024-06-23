from typing import List, Dict
from app.utils.logger import Logger

logger = Logger("controllers/run_code", log_file="run_code.log")


def buld_py_funct(py_func: str):
    try:
        locals = {}
        globals = {}
        exec(py_func, globals, locals)
        func = next(iter(locals.values()))
        return func
    except Exception as e:
        return e


def text2var(str_input: str) -> dict:
    locals = {}
    globals = {}
    try:
        exec(str_input, globals, locals)
    except Exception as e:
        logger.error(f"Error converting text to variable: {e}")
    return locals


def run_testcase(func, 
                 test_case: Dict[str, str], 
                 return_testcase: bool
                ) -> dict:
    input = text2var(test_case["input"])
    expected_output = text2var("output = "+test_case["expected_output"])["output"]
    testcase_id = str(test_case["testcase_id"])

    try:
        func_output = func(**input)
    except Exception as e:
        func_output = e

    testcase_output = {
        "testcase_id": testcase_id,
        "output": func_output,
        "is_pass": False,
    }

    if return_testcase:
        testcase_output["expected_output"] = expected_output

    if func_output == expected_output:
        testcase_output["is_pass"] = True

    return testcase_output


def test_py_funct(py_func: str, 
                  test_case: List[Dict[str, str]],
                  return_testcase: bool = False
                  ) -> List[dict]:
    func = buld_py_funct(py_func)

    if isinstance(func, Exception):
        return func
    
    testcase_outputs = []
    for case in test_case:
        testcase_outputs.append(run_testcase(func, case, return_testcase))
    return testcase_outputs