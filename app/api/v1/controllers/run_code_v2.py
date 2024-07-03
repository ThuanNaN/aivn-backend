import asyncio
from typing import List, Dict
import re
import numpy as np
import torch

from app.utils.logger import Logger
logger = Logger("controllers/run_code", log_file="run_code.log")

class BuildObject:
    REMOVE_KEYWORDS = ["os", "sys", "import", "cmd", "rm", "remove"]
    TIMEOUT_DURATION = 10 


    @staticmethod
    async def exec_code(str_input: str, admin_vars: dict = {}) -> dict:
        loop = asyncio.get_running_loop()
        local_vars = {}
        global_vars = admin_vars
        def sync_exec():
            exec(str_input, global_vars, local_vars)
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, sync_exec),
                timeout=BuildObject.TIMEOUT_DURATION
            )
        except asyncio.TimeoutError:
            logger.error("Too long to execute the code.")
        # except Exception as e:
        #     logger.error(f"Error convert to variable: {e}")
        return local_vars


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
        self.admin_vars = await BuildObject.exec_code(self.admin_code_str)
        self.class_name = self.admin_vars["class_name"]
        self.class_method = self.admin_vars["class_method"]
        self.code_str = BuildObject.remove_import_lines(self.code_str)

        error = None
        testcase_outputs = []
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

        # get testcase input

        extracted_text = re.findall(r'{(.*?)}', testcase["input"])
        init_kwargs_str = extracted_text[0].replace("|", "\n")
        input_kwargs_str = extracted_text[1].replace("|", "\n")

        try:
            init_kwargs = await BuildObject.exec_code(init_kwargs_str, self.admin_vars)
            input_kwargs = await BuildObject.exec_code(input_kwargs_str, self.admin_vars)

        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            return testcase_output
        
        # get expected output
        try:
            testcase_output_str = testcase["expected_output"]
            testcase_output_dict = await BuildObject.exec_code(testcase_output_str,
                                                            self.admin_vars)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            return testcase_output
        
        expected_output = testcase_output_dict.get("output")

        # get object variables
        try:
            object_vars = await BuildObject.exec_code(self.code_str, self.admin_vars)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            return testcase_output
        
        # build object
        try:
            my_object = object_vars.get(self.class_name)(**init_kwargs)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            return testcase_output
        

        # run method
        try:
            method = getattr(my_object, self.class_method)
            method_output = method(**input_kwargs)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            return testcase_output
        
        if method_output is None:
            testcase_output["error"] = "Output is None"
            return testcase_output
        
        testcase_output["output"] = method_output

        # check output
        try:
            is_correct = self.check_output(method_output, expected_output)
        except Exception as e:
            testcase_output["error"] = f"{type(e).__name__}: {e}"
            return testcase_output
        
        testcase_output["is_pass"] = is_correct
        return testcase_output

    def check_output(self, output, expected_output) -> bool:
        if type(expected_output) != type(output):
            raise TypeError(
                f"Expected output type {type(expected_output)} does not match function output type {type(output)}")
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
