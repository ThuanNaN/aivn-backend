from typing import List
from datetime import datetime, UTC
from app.utils import (
    MessageException,
    Logger, 
    cohort_permission,
    generate_id
)
from slugify import slugify
from fastapi import (
    APIRouter, Depends, 
    status, HTTPException
)
from app.api.v1.controllers.contest import (
    add_contest,
    retrieve_contests,
    retrieve_contest,
    retrieve_contest_detail,
    update_contest,
    delete_contest,
    retrieve_available_contests,
    retrieve_contest_by_slug,
    contest_slug_is_unique
)
from app.api.v1.controllers.exam import (
    retrieve_exam
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
    update_submission,
    retrieve_submission_by_id_user_retake
)
from app.api.v1.controllers.certificate import (
    retrieve_certificate_by_validation_id
)
from app.api.v1.controllers.user import retrieve_user
from app.schemas.submission import (
    SubmittedProblem,
    SubmissionSchema,
    SubmittedResult,
    UpdateSubmissionDB
)
from app.schemas.contest import (
    ContestSchema,
    ContestSchemaDB,
    UpdateContestSchema,
    UpdateContestSchemaDB
)
from app.schemas.exam_problem import (
    ExamProblemDB
)
from app.schemas.response import (
    ListResponseModel,
    DictResponseModel,
    ErrorResponseModel
)
from app.schemas.certificate import CertificateDB
from app.core.security import is_admin, is_authenticated
import inngest
from app.inngest.client import inngest_client


router = APIRouter()
logger = Logger("routes/contest", log_file="contest.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Create a new contest")
async def create_contest(contest: ContestSchema, 
                         creator_id=Depends(is_authenticated)):
    contest_slug = slugify(contest.title)
    # Check meeting_slug is unique
    is_unique = await contest_slug_is_unique(contest_slug)
    if isinstance(is_unique, Exception):
        raise HTTPException(
            status_code=is_unique.status_code,
            detail=str(is_unique)
        )
    contest_dict = ContestSchemaDB(
        **contest.model_dump(), 
        creator_id=creator_id,
        slug=contest_slug,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    ).model_dump()
    new_contest = await add_contest(contest_dict)
    if isinstance(new_contest, MessageException):
        return ErrorResponseModel(error=str(new_contest),
                                  message="An error occurred.",
                                  code=status.HTTP_404_NOT_FOUND)
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
                                      creator_id=clerk_user_id,
                                      created_at=datetime.now(UTC),
                                      updated_at=datetime.now(UTC))
    new_exam_problem = await add_exam_problem(exam_problem_dict.model_dump())
    if isinstance(new_exam_problem, MessageException):
        return ErrorResponseModel(error=str(new_exam_problem),
                                  message="An error occurred.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=new_exam_problem,
                             message="ExamProblem added successfully.",
                             code=status.HTTP_200_OK)


@router.post("/exam/{exam_id}/submit",
             description="Submit problems to a contest")
async def create_submission(exam_id: str,
                            submission_data: SubmissionSchema,
                            clerk_user_id: str = Depends(is_authenticated)):
    # Check the exam still open (is active)
    exam_info = await retrieve_exam(exam_id, clerk_user_id)
    if isinstance(exam_info, MessageException):
        raise HTTPException(
            status_code=exam_info.status_code,
            detail=exam_info.message
        )
    if exam_info["is_active"] is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The exam is not active."
        )
    # Check the contest still open (is active)
    contest_info = await retrieve_contest(exam_info["contest_id"], clerk_user_id)
    if isinstance(contest_info, MessageException):
        raise HTTPException(
            status_code=contest_info.status_code,
            detail=contest_info.message
        )
    if contest_info["is_active"] is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The contest is not active."
        )
    
    # Check the user is allowed to submit
    user_info = await retrieve_user(clerk_user_id)
    if isinstance(user_info, MessageException):
        raise HTTPException(
            status_code=user_info.status_code,
            detail=user_info.message
        )
    
    if not cohort_permission(user_info["cohort"], contest_info["cohorts"]):
        raise HTTPException(
            detail="You are not allowed to submit this exam.",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    submitted_problems: List[SubmittedProblem] | None = submission_data.submitted_problems

    if submitted_problems is None:
        submitted_results = None
    else:
        submitted_results = []
        TOTAL_SCORE = 0
        MAX_SCORE = 0
        TOTAL_PASSED = 0
        for submitted_problem in submitted_problems:
            problem_id = submitted_problem.problem_id
            problem_info = await retrieve_problem(problem_id, full_return=True)
            if isinstance(problem_info, MessageException):
                return HTTPException(
                    status_code=problem_info.status_code,
                    detail=problem_info.message
                )
            MAX_SCORE += problem_info["problem_score"]
            submitted_code = submitted_problem.submitted_code
            public_results, private_results = None, None
            if submitted_code is not None:
                admin_template = problem_info.get("admin_template", "")
                public_testcases = problem_info.get("public_testcases", [])
                private_testcases = problem_info.get("private_testcases", [])

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

                is_pass_problem = is_pass_public and is_pass_private
                if is_pass_problem:
                    TOTAL_SCORE += problem_info["problem_score"]
                    TOTAL_PASSED += 1 

            submitted_choice = submitted_problem.submitted_choice
            if submitted_choice is not None:
                choice_answers = submitted_choice.split(",")  # -> ["id_1", "id_2"]
                true_answers_id = [str(choice["choice_id"])
                                for choice in problem_info["choices"]
                                if choice["is_correct"]]

                if len(choice_answers) != len(true_answers_id):
                    is_pass_problem = False
                else:
                    is_pass_problem = sorted(
                        choice_answers) == sorted(true_answers_id)
                
                if is_pass_problem:
                    TOTAL_SCORE += problem_info["problem_score"]
                    TOTAL_PASSED += 1

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

    # Upsert submission to database
    pseudo_submission = await retrieve_submission_by_id_user_retake(exam_id=exam_id,
                                                                    clerk_user_id=clerk_user_id,
                                                                    retake_id=submission_data.retake_id,
                                                                    check_none=False)
    if isinstance(pseudo_submission, MessageException):
        return HTTPException(
            status_code=pseudo_submission.status_code,
            detail=pseudo_submission.message
        )

    upsert_submission = UpdateSubmissionDB(
        retake_id=submission_data.retake_id,
        submitted_problems=submitted_results,
        total_score=TOTAL_SCORE,
        max_score=MAX_SCORE,
        total_problems=len(submitted_problems),
        total_problems_passed=TOTAL_PASSED,
        created_at=datetime.now(UTC)
    ).model_dump()

    updated_submission = await update_submission(pseudo_submission["id"], 
                                                 upsert_submission)
    if isinstance(updated_submission, MessageException):
        raise HTTPException(
            status_code=updated_submission.status_code,
            detail=updated_submission.message
        )
    
    if (contest_info["certificate_template"] is not None 
    and MAX_SCORE > 0 
    and TOTAL_SCORE / MAX_SCORE >= 0.5):
        validation_id = generate_id()
        # Check if validation_id is exist
        while await retrieve_certificate_by_validation_id(validation_id):
            validation_id = generate_id()

        # Create a new certificate
        certificate_data = CertificateDB(
            validation_id=validation_id,
            clerk_user_id=clerk_user_id,
            submission_id=pseudo_submission["id"],
            result_score=f"{TOTAL_SCORE}/{MAX_SCORE}",
            template=contest_info["certificate_template"],
            created_at=datetime.now(UTC).isoformat()
        ).model_dump()

        # Send event to inngest
        await inngest_client.send(
            inngest.Event(
                name="contest/certificate",
                id=f"certificate-{validation_id}",
                data={
                    "user_info": {
                        "fullname": user_info["fullname"],
                        "email": user_info["email"]
                    },
                    "certificate_info": certificate_data
                }
            )
        )

    return DictResponseModel(
        data={
            "total_score": TOTAL_SCORE,
            "max_score": MAX_SCORE,
            "total_problems": len(submitted_problems),
            "total_problems_passed": TOTAL_PASSED
        },
        message="Submission added successfully.",
        code=status.HTTP_201_CREATED)
    

@router.get("/contests",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Retrieve all contests")
async def get_contests():
    contests = await retrieve_contests()
    if isinstance(contests, MessageException):
        return ErrorResponseModel(error=str(contests),
                                  message="Error when retrieve contests.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=contests,
                             message="Contests retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/contest/instruction/{slug}",
            description="Retrieve a contest instruction with a matching slug")
async def get_contest_instruction(slug: str, clerk_user_id: str = Depends(is_authenticated)):
    contest = await retrieve_contest_by_slug(slug, clerk_user_id)
    if isinstance(contest, MessageException):
        return HTTPException(
            status_code=contest.status_code,
            detail=contest.message
        )
    return_data = {
        "title": contest["title"],
        "description": contest["description"],
        "instruction": contest["instruction"],
    }
    return DictResponseModel(data=return_data,
                             message="Contest instruction retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/available",
            description="Retrieve all available contests")
async def get_available_contests(clerk_user_id: str = Depends(is_authenticated)):
    contests = await retrieve_available_contests(clerk_user_id)
    if isinstance(contests, MessageException):
        return ErrorResponseModel(error=contests.message,
                                  message="Error when retrieve contests.",
                                  code=contests.status_code)
    return ListResponseModel(data=contests,
                             message="Contests retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}",
            description="Retrieve a contest with a matching ID")
async def get_contest(id: str, clerk_user_id: str = Depends(is_authenticated)):
    contest = await retrieve_contest(id, clerk_user_id)
    if isinstance(contest, MessageException):
        return ErrorResponseModel(error=contest.message,
                                  message="An error occurred.",
                                  code=contest.status_code)
    return DictResponseModel(data=contest,
                             message="Contest retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.get("/{id}/details",
            description="Retrieve a contest with a matching ID and its details")
async def get_contest_detail(id: str, clerk_user_id: str = Depends(is_authenticated)):
    contest_details = await retrieve_contest_detail(id, clerk_user_id)
    if isinstance(contest_details, MessageException):
        return ErrorResponseModel(error=str(contest_details),
                                  message="An error occurred.",
                                  code=status.HTTP_404_NOT_FOUND)
    return DictResponseModel(data=contest_details,
                             message="Contest retrieved successfully.",
                             code=status.HTTP_200_OK)


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            tags=["Admin"],
            description="Update a contest with a matching ID")
async def update_contest_data(id: str, 
                              contest: UpdateContestSchema,
                              creator_id=Depends(is_authenticated)):
    contest_slug = slugify(contest.title)
    # Check meeting_slug is unique
    is_unique = await contest_slug_is_unique(contest_slug, is_update=True)
    if isinstance(is_unique, Exception):
        raise HTTPException(
            status_code=is_unique.status_code,
            detail=str(is_unique)
        )
    contest_dict = UpdateContestSchemaDB(
        **contest.model_dump(),
        creator_id=creator_id,
        slug=contest_slug,
        updated_at = datetime.now(UTC)
    ).model_dump()
    updated_contest = await update_contest(id, contest_dict)
    if isinstance(updated_contest, MessageException):
        return ErrorResponseModel(error=str(updated_contest),
                                  message="An error occurred.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not updated_contest:
        return ErrorResponseModel(error="No contests were updated.",
                                  message="An error occurred when update contest.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=[],
                             message="Contest updated successfully.",
                             code=status.HTTP_200_OK)


@router.delete("/exam/{exam_id}/problems/{problem_id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Remove exam-problem")
async def delete_exam_problem_data(exam_id: str, problem_id: str):
    exam_problem = await retrieve_by_exam_problem_id(exam_id, problem_id)
    if isinstance(exam_problem, MessageException):
        return ErrorResponseModel(error=str(exam_problem),
                                  message="An error occurred while retrieve exam-problem.",
                                  code=status.HTTP_404_NOT_FOUND)
    deleted_exam_problem = await delete_exam_problem(exam_problem["id"])
    if isinstance(deleted_exam_problem, MessageException):
        return ErrorResponseModel(error=str(deleted_exam_problem),
                                  message="An error occurred while delete exam-problem.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not deleted_exam_problem:
        return ErrorResponseModel(error="No exam-problems were deleted.",
                                  message="An error occurred when delete exam-problem.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=[],
                             message="Exam-problem deleted successfully.",
                             code=status.HTTP_200_OK)


@router.delete("/{id}",
               dependencies=[Depends(is_admin)],
               tags=["Admin"],
               description="Delete a contest with a matching ID")
async def delete_contest_data(id: str):
    delete_result = await delete_contest(id)
    if isinstance(delete_result, MessageException):
        return ErrorResponseModel(error=str(delete_result),
                                  message="An error occurred when delete contest.",
                                  code=status.HTTP_404_NOT_FOUND)
    if not delete_result:
        return ErrorResponseModel(error="No contests were updated.",
                                  message="An error occurred when delete contest.",
                                  code=status.HTTP_404_NOT_FOUND)
    return ListResponseModel(data=[],
                             message="Contest deleted successfully.",
                             code=status.HTTP_200_OK)
