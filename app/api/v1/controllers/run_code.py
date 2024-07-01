from typing import List, Dict
import numpy as np
# import torch
from app.utils.logger import Logger

logger = Logger("controllers/run_code", log_file="run_code.log")

rm_keys = ["os", "sys", "import", "cmd", "rm", "remove"]


def remove_import_lines(code: str,
                        key_word: List[str] = rm_keys
                        ) -> str:
    lines = code.split('\n')
    result_lines = []
    for line in lines:
        if not any(keyword in line for keyword in key_word):
            result_lines.append(line)
    return '\n'.join(result_lines)

def check_output(expected_out, funct_out) -> bool:
    if type(expected_out) != type(funct_out):
        raise TypeError(f"Expected output type {type(expected_out)} \
                        does not match function output type {type(funct_out)}")

    if isinstance(expected_out, (int, float)):
        return expected_out == funct_out
    elif isinstance(expected_out, (list, tuple)):
        return all(check_output(i, o) for i, o in zip(expected_out, funct_out))
    elif isinstance(expected_out, np.ndarray):
        return np.array_equal(expected_out, funct_out)
    elif isinstance(expected_out, dict):
        if expected_out.keys() != funct_out.keys():
            return False
        return all(check_output(expected_out[k], funct_out[k]) for k in expected_out)
    # elif isinstance(input_value, torch.Tensor):
    #     return torch.equal(input_value, output_value)
    else:
        raise TypeError(f"Unsupported input type: {type(expected_out)}")


def map_values_to_string(input_dict):
    return {key: str(value) for key, value in input_dict.items()}


def text2var(str_input: str, admin_locals: dict = {}) -> dict:
    locals = {}
    globals = admin_locals
    try:
        exec(str_input, globals, locals)
    except Exception as e:
        logger.error(f"Error converting text to variable: {e}")
    return locals


def run_testcase(admin_template: str,
                 py_func: str,
                 testcase: Dict[str, str],
                 return_testcase: bool
                 ) -> dict:
    admin_locals = text2var(admin_template)
    input = text2var(testcase["input"], admin_locals)
    str_input = "output = " + testcase["expected_output"]
    output_var = text2var(str_input, admin_locals)
    expected_output = output_var["output"]
    testcase_id = str(testcase["testcase_id"])

    testcase_output = {
        "testcase_id": testcase_id,
        "input": map_values_to_string(input),
        "output": None,
        "is_pass": False,
        "error": None
    }
    if return_testcase:
        testcase_output["expected_output"] = testcase["expected_output"]
    try:
        locals = {}
        globals = admin_locals
        exec(py_func, globals, locals)
        if len(locals) > 1:
            raise Exception("Multiple functions found in the code. \
                             Only one function is allowed.")
        generated_function = next(iter(locals.values()))
        func_output = generated_function(**input)
        testcase_output["output"] = repr(func_output)
        testcase_output["is_pass"] = check_output(expected_output, func_output)
    except Exception as e:
        testcase_output["error"] = f"{type(e).__name__}: {e}"

    return testcase_output


def test_py_funct(admin_template: str,
                  py_func: str,
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
        run_output = run_testcase(admin_template,
                                  py_func,
                                  testcase,
                                  return_testcase)
        testcase_outputs.append(run_output)
        if run_output["error"] is not None:
            test_info["error"] = run_output["error"]
            if not run_all:
                break
    test_info["testcase_outputs"] = testcase_outputs
    return test_info
