from app.utils.logger import Logger
from fastapi import APIRouter, Depends, status
from app.api.v1.controllers.contest import (
    add_contest,
    retrieve_contests,
    retrieve_contest,
    retrieve_contest_detail,
    update_contest,
    delete_contest,
    retrieve_available_contests
)
from app.api.v1.controllers.problem import (
    retrieve_problem
)
from app.api.v1.controllers.exam_problem import (
    add_exam_problem,
    retrieve_by_exam_problem_id,
    delete_exam_problem
)
from app.api.v1.controllers.run_code import (
    run_testcases
)
from app.api.v1.controllers.submission import (
    add_submission,
)
from app.schemas.submission import (
    Submission,
    SubmittedResult,
    SubmissionDB
)
from app.schemas.contest import (
    ContestSchema,
    UpdateContestSchema,
)
from app.schemas.exam_problem import (
    ExamProblemDB
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.core.security import is_admin, is_authenticated

router = APIRouter()
logger = Logger("routes/contest", log_file="contest.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Create a new contest")
async def create_contest(contest: ContestSchema):
    contest_dict = contest.model_dump()
    new_contest = await add_contest(contest_dict)
    return DictResponseModel(data=new_contest,
                             message="Contest created successfully.",
                             code=status.HTTP_200_OK)


@router.post("/exam/{exam_id}/problems",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new exam_problem")
async def create_exam_problem(exam_id: str,
                              problem_id: str,
                              index: int,
                              clerk_user_id=Depends(is_authenticated)):
    exam_problem_dict = ExamProblemDB(exam_id=exam_id,
                                      problem_id=problem_id,
                                      index=index,
                                      creator_id=clerk_user_id)
    new_exam_problem = await add_exam_problem(exam_problem_dict.model_dump())
    return DictResponseModel(data=new_exam_problem,
                             message="ExamProblem added successfully.",
                             code=status.HTTP_200_OK)


@router.post("/exam/{exam_id}/submit",
                dependencies=[Depends(is_authenticated)],
                description="Submit problems to a contest")
async def create_submission(exam_id: str,
                            submission_data: Submission,
                            clerk_user_id: str = Depends(is_authenticated)):
    submission_dict = submission_data.model_dump()
    submitted_problems = submission_dict["submitted_problems"]
    
    submitted_results = []
    total_score = 0
    for submitted_problem in submitted_problems:
        problem_id = submitted_problem["problem_id"]
        problem_info = await retrieve_problem(problem_id, full_return=True)
        if not problem_info:
            logger.error(f'Problem with ID {problem_id} not found.')
            return ErrorResponseModel(error="Error when submit code.",
                                      message="Problem not found.",
                                      code=status.HTTP_404_NOT_FOUND)
       
        submitted_code = submitted_problem.get("submitted_code", None)
        public_results, private_results = None, None
        if submitted_code is not None:
            admin_template = problem_info.get("admin_template", "")
            public_testcases = problem_info.get("public_testcases", [])
            private_testcases = problem_info.get("private_testcases", [])

            print("private_results: ", private_testcases)


            public_results, is_pass_public = await run_testcases(
                admin_template,
                submitted_code,
                public_testcases
            )

            private_results, is_pass_private = await run_testcases(
                admin_template,
                submitted_code,
                private_testcases
            )
            print("private_results: ", private_results)


            is_pass_problem = is_pass_public and is_pass_private
            total_score += int(is_pass_problem)


        submitted_choice = submitted_problem.get("submitted_choice", None)
        if submitted_choice is not None:
            choice_answers = submitted_choice.split(",")  # -> ["id_1", "id_2"]
            true_answers_id = [str(choice["choice_id"])
                               for choice in problem_info["choices"]
                               if choice["is_correct"]]

            if len(choice_answers) != len(true_answers_id):
                is_pass_problem = False
            else:
                is_pass_problem = sorted(choice_answers) == sorted(true_answers_id)
            total_score += int(is_pass_problem)

        submitted_results.append(
            SubmittedResult(
                problem_id=problem_id,
                submitted_code=submitted_code,
                submitted_choice=submitted_choice,
                title=problem_info["title"],
                description=problem_info["description"],
                public_testcases_results=public_results,
                private_testcases_results=private_results,
                choice_results=problem_info["choices"],
                is_pass_problem=is_pass_problem
            )
        )
    
    submission_db = SubmissionDB(
        exam_id = exam_id,
        clerk_user_id=clerk_user_id,
        retake_id=submission_dict.get("retake_id", None),
        submitted_problems = submitted_results
    )

    try:
        _ = await add_submission(submission_db.model_dump())
        return DictResponseModel(
            data={
                "total_score": total_score,
                "total_problems": len(submitted_problems)
            },
            message="Submission added successfully.",
            code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f'Error when submit code: {e}')
        return ErrorResponseModel(error="Error when submit code.",
                                  message="Submission not created.",
                                  code=status.HTTP_404_NOT_FOUND)


@router.get("/contests",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all contests")
async def get_contests():
    contests = await retrieve_contests()
    if contests:
        return ListResponseModel(data=contests,
                                 message="Contests retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when retrieve contests.",
                              message="Contests not found.",
                              code=status.HTTP_404_NOT_FOUND)

@router.get("/available",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all available contests")
async def get_available_contests(user_clerk_id: str = Depends(is_authenticated)):
    contests = await retrieve_available_contests(user_clerk_id)
    if contests:
        return ListResponseModel(data=contests,
                                 message="Contests retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when retrieve contests.",
                              message="Contests not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a contest with a matching ID")
async def get_contest(id: str):
    contest = await retrieve_contest(id)
    if contest:
        return DictResponseModel(data=contest,
                                 message="Contest retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when retrieve contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.get("/{id}/details",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a contest with a matching ID and its details")
async def get_contest_detail(id: str, user_clerk_id: str = Depends(is_authenticated)):
    contest_details = await retrieve_contest_detail(id, user_clerk_id)
    if contest_details:
        return DictResponseModel(data=contest_details,
                                 message="Contest retrieved successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when retrieve contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a contest with a matching ID")
async def update_contest_data(id: str, contest: UpdateContestSchema):
    contest_dict = contest.model_dump()
    updated = await update_contest(id, contest_dict)
    if updated:
        return ListResponseModel(data=[],
                                 message="Contest updated successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when update contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/exam/{exam_id}/problems/{problem_id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Remove exam-problem")
async def delete_exam_problem_data(exam_id: str, problem_id: str):
    exam_problem = await retrieve_by_exam_problem_id(exam_id, problem_id)
    if exam_problem:
        deleted = await delete_exam_problem(exam_problem["id"])
        if deleted:
            return ListResponseModel(data=[],
                                     message="ExamProblem deleted successfully.",
                                     code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when delete exam_problem.",
                              message="ExamProblem not found.",
                              code=status.HTTP_404_NOT_FOUND)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a contest with a matching ID")
async def delete_contest_data(id: str):
    deleted = await delete_contest(id)
    if deleted:
        return ListResponseModel(data=[],
                                 message="Contest deleted successfully.",
                                 code=status.HTTP_200_OK)
    return ErrorResponseModel(error="Error when delete contest.",
                              message="Contest not found.",
                              code=status.HTTP_404_NOT_FOUND)
