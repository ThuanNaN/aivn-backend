from typing import List, Dict
from app.utils.logger import Logger

logger = Logger("controllers/run_code", log_file="run_code.log")


def remove_import_lines(code: str, 
                        key_word: List[str] = ["os", "sys", "import"]
                        ) -> str:
    lines = code.split('\n')
    result_lines = []

    for line in lines:
        if not any(keyword in line for keyword in key_word):
            result_lines.append(line)
    
    return '\n'.join(result_lines)


def text2var(str_input: str) -> dict:
    locals = {}
    globals = {}
    try:
        exec(str_input, globals, locals)
    except Exception as e:
        logger.error(f"Error converting text to variable: {e}")
    return locals

def run_testcase(py_func: str, 
                 testcase: Dict[str, str], 
                 return_testcase: bool
                ) -> dict:
    input = text2var(testcase["input"])
    expected_output = text2var("output = "+testcase["expected_output"])["output"]
    testcase_id = str(testcase["testcase_id"])

    testcase_output = {
        "testcase_id": testcase_id,
        "input": input,
        "output": None,
        "is_pass": False,
        "error": None
    }
    if return_testcase:
        testcase_output["expected_output"] = expected_output

    try:
        locals = {}
        globals = {}
        exec(py_func, globals, locals)
        if len(locals) > 1:
            raise Exception("Multiple functions found in the code. Only one function is allowed.")
        funct = next(iter(locals.values()))
        func_output = funct(**input)
    except Exception as e:
        testcase_output["error"] = f"{type(e).__name__}: {e}"
        return testcase_output

    testcase_output["output"] = func_output

    if func_output == expected_output:
        testcase_output["is_pass"] = True

    return testcase_output


def test_py_funct(py_func: str, 
                  testcases: List[Dict[str, str]],
                  return_testcase: bool = False,
                  run_all: bool = False
                  ) -> dict:
    py_func = remove_import_lines(py_func)
    test_info = {
        "testcase_outputs": [],
        "error": None
    }
    testcase_outputs = []
    for testcase in testcases:
        run_output = run_testcase(py_func, testcase, return_testcase)
        testcase_outputs.append(run_output)
        if run_output["error"] is not None:
            test_info["error"] = run_output["error"]
            if not run_all:
                break    
    test_info["testcase_outputs"] = testcase_outputs
    return test_info