from typing import List, Dict
from app.utils.logger import Logger

logger = Logger("controllers/run_code", log_file="run_code.log")


def buld_py_funct(py_func: str) -> callable:
    locals = {}
    globals = {}
    exec(py_func, globals, locals)
    func = next(iter(locals.values()))
    return func


def text2var(str_input: str) -> dict:
    locals = {}
    globals = {}
    try:
        exec(str_input, globals, locals)
    except Exception as e:
        print(e)
        print("str_input: ", str_input, type(str_input))
    return locals


def run_testcase(func, test_case: Dict[str, str]) -> dict:
    input = text2var(test_case["input"])
    expected_output = text2var("output = "+test_case["expected_output"])["output"]
    testcase_id = str(test_case["testcase_id"])
    testcase_output = {
        "testcase_id": testcase_id,
        "is_pass": False,
    }
    func_output = func(**input)
    if func_output == expected_output:
        testcase_output["is_pass"] = True
    else:
        print(func_output)
        print(expected_output)
    return testcase_output


def test_py_funct(py_func: str, 
                  test_case: List[Dict[str, str]]
                  ) -> List[dict]:
    func = buld_py_funct(py_func)
    testcase_outputs = []
    for case in test_case:
        testcase_outputs.append(run_testcase(func, case))
        return testcase_outputs