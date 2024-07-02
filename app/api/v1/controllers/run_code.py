from typing import List, Dict
import asyncio
import numpy as np
# import torch
from app.utils.logger import Logger

logger = Logger("controllers/run_code", log_file="run_code.log")
REMOVE_KEYWORDS = ["os", "sys", "import", "cmd", "rm", "remove"]
TIMEOUT_DURATION = 10  # seconds


def remove_import_lines(code: str,
                        key_word: List[str] = REMOVE_KEYWORDS
                        ) -> str:
    lines = code.split('\n')
    result_lines = []
    for line in lines:
        if not any(keyword in line for keyword in key_word):
            result_lines.append(line)
    return '\n'.join(result_lines)


def check_output(expected_out, funct_out) -> bool:
    if type(expected_out) != type(funct_out):
        raise TypeError(
            f"Expected output type {type(expected_out)} does not match function output type {type(funct_out)}")

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


async def exec_code(str_input: str, admin_locals: dict = {}) -> dict:
    loop = asyncio.get_running_loop()
    locals = {}
    globals = admin_locals
    def sync_exec():
        exec(str_input, globals, locals)

    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, sync_exec),
            timeout=TIMEOUT_DURATION
        )
    except asyncio.TimeoutError:
        logger.error("Too long to execute the code.")
    except Exception as e:
        logger.error(f"Error convert to variable: {e}")
    return locals


async def run_testcase(admin_template: str,
                       py_func: str,
                       testcase: Dict[str, str],
                       return_testcase: bool
                       ) -> dict:
    testcase_output = {
        "testcase_id": str(testcase["testcase_id"]),
        "input": testcase["input"],
        "output": None,
        "is_pass": False,
        "error": None
    }
    if return_testcase:
        testcase_output["expected_output"] = testcase["expected_output"]

    try:
        admin_locals = await exec_code(admin_template)
        input = await exec_code(testcase["input"], admin_locals)
        str_input = "output = " + testcase["expected_output"]
        output_var = await exec_code(str_input, admin_locals)
        expected_output = output_var["output"]
    except Exception as e:
        testcase_output["error"] = f"{type(e).__name__}: {e}"
        return testcase_output

    try:
        locals = await exec_code(py_func, admin_locals)
        if len(locals) > 1:
            raise Exception(
                "Multiple functions found in the code. Only one function is allowed.")
        generated_function = next(iter(locals.values()))
        func_output = generated_function(**input)

    except Exception as e:
        testcase_output["error"] = f"{type(e).__name__}: {e}"

    try:
        testcase_output["output"] = repr(func_output)
        testcase_output["is_pass"] = check_output(expected_output, func_output)
    except Exception as e:
        testcase_output["error"] = f"{type(e).__name__}: {e}"

    return testcase_output


async def test_py_funct(admin_template: str,
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
        run_output = await run_testcase(admin_template,
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
