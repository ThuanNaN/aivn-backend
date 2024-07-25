import asyncio
import traceback
from typing import List, Dict
import re
import numpy as np
import torch

from app.utils.logger import Logger
logger = Logger("controllers/run_code", log_file="run_code.log")


class BuildObject:
    REMOVE_KEYWORDS = ["os", "sys", "import", "cmd", "rm", "remove", "del", "delete"]
    TIMEOUT_DURATION = 10

    @staticmethod
    async def exec_code(str_input: str, admin_vars: dict = {}) -> dict:
        loop = asyncio.get_running_loop()
        local_vars = {}
        global_vars = admin_vars
        error = None

        def sync_exec():
            exec(str_input, global_vars, local_vars)
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, sync_exec),
                timeout=BuildObject.TIMEOUT_DURATION
            )
        except asyncio.TimeoutError:
            # logger.error("Too long to execute the code.")
            error = "Too long to execute the code."
        except Exception as e:
            logger.error(f"Error convert to variable: {e}")
            # error = f"{type(e).__name__}: {e}"
            track_error = traceback.format_exc()
            error = track_error.split("exec(str_input, global_vars, local_vars)\n")[-1]
        return {
            "error": error,
            "local_vars": local_vars
        }

    @staticmethod
    def remove_import_lines(code_str: str) -> str:
        lines = code_str.split('\n')
        result_lines = []
        for line in lines:
            if not any(keyword in line for keyword in BuildObject.REMOVE_KEYWORDS):
                result_lines.append(line)
        return '\n'.join(result_lines)


class TestPythonFunction:
    def __init__(self,
                 admin_code_str: str,
                 code_str: str,
                 testcases: List[Dict[str, str]],
                 return_testcase: bool = False,
                 run_all: bool = False
                 ) -> None:
        self.admin_code_str = admin_code_str
        self.code_str = code_str
        self.testcases = testcases
        self.return_testcase = return_testcase
        self.run_all = run_all

    async def run_all_testcases(self) -> dict:
        error = None
        testcase_outputs = []

        # get admin variables
        admin_templates = await BuildObject.exec_code(self.admin_code_str)
        if admin_templates["error"] is not None:
            return {
                "testcase_outputs": testcase_outputs,
                "error": "Exec admin template error: " + admin_templates["error"]
            }
        self.admin_vars = admin_templates["local_vars"]

        # get class name and method
        self.class_name = self.admin_vars["class_name"]
        self.class_method = self.admin_vars["class_method"]

        # remove import lines in code_str
        self.code_str = BuildObject.remove_import_lines(self.code_str)

        # run all testcases
        for testcase in self.testcases:
            run_one_output = await self.run_one_testcase(testcase)
            testcase_outputs.append(run_one_output)
            if run_one_output["error"]:
                error = run_one_output["error"]
                if not self.run_all:
                    break
        return {
            "testcase_outputs": testcase_outputs,
            "error": error
        }

    async def run_one_testcase(self, testcase: Dict[str, str]) -> dict:
        testcase_output = {
            "testcase_id": str(testcase["testcase_id"]),
            "input": testcase["input"],
            "output": None,
            "is_pass": False,
            "error": None
        }
        if self.return_testcase:
            testcase_output["expected_output"] = testcase["expected_output"]

        # input_kwargs
        build_input_kwargs = await BuildObject.exec_code(testcase["input"], self.admin_vars)
        if build_input_kwargs["error"] is not None:
            testcase_output["error"] = build_input_kwargs["error"]
            return testcase_output
        input_kwargs = build_input_kwargs["local_vars"]

        # get expected output
        testcase_output_str = "expected_output = " + testcase["expected_output"]
        build_testcase_output = await BuildObject.exec_code(testcase_output_str, self.admin_vars)

        if build_testcase_output["error"] is not None:
            testcase_output["error"] = build_testcase_output["error"]
            return testcase_output
        expected_output = build_testcase_output["local_vars"].get("expected_output")

        # get object variables
        build_object_vars = await BuildObject.exec_code(self.code_str, self.admin_vars)
        if build_object_vars["error"] is not None:
            testcase_output["error"] = build_object_vars["error"]
            testcase_output["output"] = build_object_vars["error"]
            return testcase_output
        object_vars = build_object_vars["local_vars"]
        
        # build object
        try:
            my_object = object_vars.get(self.class_name)()
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            testcase_output["output"] = f"{type(e).__name__}: {e}"
            return testcase_output

        # run method
        try:
            method = getattr(my_object, self.class_method)
            method_output = method(**input_kwargs)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            testcase_output["output"] = f"{type(e).__name__}: {e}"
            return testcase_output

        if method_output is None:
            testcase_output["error"] = "Output is None"
            testcase_output["output"] = "None"
            return testcase_output

        testcase_output["output"] = repr(method_output)

        # check output
        try:
            is_correct = self.check_output(method_output, expected_output)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            testcase_output["output"] = f"{type(e).__name__}: {e}"
            return testcase_output

        testcase_output["is_pass"] = is_correct
        return testcase_output

    def check_output(self, output, expected_output) -> bool:
        if type(expected_output) != type(output):
            raise TypeError(
                f"Expected output type {type(expected_output)} does not match Output type {type(output)}")
        if isinstance(expected_output, (int, float)):
            return expected_output == output
        elif isinstance(expected_output, (list, tuple)):
            return all(self.check_output(i, o) for i, o in zip(expected_output, output))
        elif isinstance(expected_output, np.ndarray):
            return np.array_equal(expected_output, output)
        elif isinstance(expected_output, dict):
            if expected_output.keys() != output.keys():
                return False
            return all(self.check_output(expected_output[k], output[k]) for k in expected_output)
        elif isinstance(expected_output, str):
            return expected_output == output
        elif isinstance(expected_output, torch.Tensor):
            return torch.equal(expected_output, output)
        else:
            raise TypeError(f"Unsupported input type: {type(expected_output)}")

async def run_testcases(admin_template: str, 
                        code: str, 
                        testcases: list,
                        return_testcase: bool = True,
                        run_all: bool = True, 
                        return_details: bool = True) -> list:
    """
    Run testcases for a problem
    :param admin_template: str
    :param code: str
    :param testcases: list
    :param return_testcase: bool
    :param run_all: bool
    :return: list, bool
    """
    if not testcases:
        return [], True
    results_dict = await TestPythonFunction(admin_template,
                                            code,
                                            testcases,
                                            return_testcase=return_testcase,
                                            run_all=run_all
                                            ).run_all_testcases()
    if not return_details:
        result = results_dict["testcase_outputs"]
        error = results_dict["error"]
        return result, error

    return_dict = []
    is_pass_testcases = True
    for i, result in enumerate(results_dict["testcase_outputs"]):
        return_dict.append(
            {
                "input": testcases[i]["input"],
                "output": str(result["output"]),
                "expected_output": testcases[i]["expected_output"],
                "error": result["error"],
                "is_pass": result["is_pass"]
            }
        )

        if not result["is_pass"]:
            is_pass_testcases = False

    return return_dict, is_pass_testcases

