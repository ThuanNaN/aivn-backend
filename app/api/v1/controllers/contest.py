from typing import List
import traceback
from app.utils import (
    MessageException,
    Logger,
    utc_to_local,
    cohort_permission
)
from fastapi import status
from app.core.database import mongo_db
from bson.objectid import ObjectId
from app.api.v1.controllers.cohort_permission import is_contest_permission
from app.api.v1.controllers.exam import (
    retrieve_exams_by_contest,
    delete_all_by_contest_id
)
from app.api.v1.controllers.exam_problem import (
    retrieve_by_exam_id
)
from app.api.v1.controllers.retake import (
    retrieve_retakes_by_user_exam_id
)
from app.api.v1.controllers.run_code import (
    run_testcases
)
from app.api.v1.controllers.problem import (
    retrieve_problem
)
from app.schemas.submission import (
    SubmittedProblem,
    SubmittedResult,
)

logger = Logger("controllers/contest", log_file="contest.log")

try:
    contest_collection = mongo_db["contests"]
    exam_collection = mongo_db["exams"]
    user_collection = mongo_db["users"]
except Exception as e:
    logger.error(f"Error when connect to collection: {e}")
    exit(1)


# helper
def contest_helper(contest) -> dict:
    return {
        "id": str(contest["_id"]),
        "title": contest["title"],
        "description": contest["description"],
        "instruction": contest["instruction"],
        "is_active": contest["is_active"],
        "cohorts": contest["cohorts"],
        "certificate_template": contest["certificate_template"],
        "creator_id": contest["creator_id"],
        "slug": contest["slug"],
        "created_at": utc_to_local(contest["created_at"]),
        "updated_at": utc_to_local(contest["updated_at"])
    }


async def add_contest(contest_data: dict) -> dict:
    """
    Create a new contest
    :param contest_data: dict
    :return: dict
    """
    try:
        contest = await contest_collection.insert_one(contest_data)
        new_contest = await contest_collection.find_one({"_id": contest.inserted_id})
        return contest_helper(new_contest)
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when add contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)



async def retrieve_contests() -> list[dict]:
    """
    Retrieve all contests in database, and sort by created_at
    :return: list[dict]
    """
    try:
        contests = []
        async for contest in contest_collection.find():
            contests.append(contest_helper(contest))
        contests.sort(key=lambda x: x["created_at"], reverse=True)
        return contests
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contests",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_available_contests(clerk_user_id: str) -> list | MessageException:
    """
    Retrieve all available contests
    :return: list[dict]
    """
    try:
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        feasible_cohort = user_info["feasible_cohort"]
        cohort_matchs = [
            { "cohorts": { "$exists": False } },
            { "cohorts": None },
            { "cohorts": { "$in": feasible_cohort } }
        ]
        pipeline = [
            {
                "$match": {
                    "is_active": True,
                    "$or": cohort_matchs
                }
            }
        ]
        result = await contest_collection.aggregate(pipeline).to_list(length=None)

        contests = []
        for contest in result:
            contest_detail = await retrieve_contest_detail(contest["_id"], clerk_user_id)
            if isinstance(contest_detail, MessageException):
                continue
            contests.append(contest_detail)
        return contests
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contests",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_contest(id: str, clerk_user_id: str) -> dict:
    """
    Retrieve a contest with a matching ID
    :param contest_id: str
    :return: dict
    """
    try:
        contest_permission = await is_contest_permission(id, clerk_user_id, return_item=True)
        if isinstance(contest_permission, MessageException):
            return contest_permission
        contest, permission = contest_permission
        if not permission:
            raise MessageException("You are not allowed to access this contest",
                                   status.HTTP_403_FORBIDDEN)
        return contest_helper(contest)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_contest_by_slug(slug: str, 
                                   clerk_user_id: str
                                   ) -> dict | MessageException:
    """
    Retrieve a contest with a matching slug
    :param slug: str
    :return: dict
    """
    try:
        user_info = await user_collection.find_one({"clerk_user_id": clerk_user_id})
        if not user_info:
            raise MessageException("User not found", 
                                   status.HTTP_404_NOT_FOUND)
        contest = await contest_collection.find_one({"slug": slug})
        if not contest:
             raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        if not cohort_permission(user_info["cohort"], contest["cohorts"]):
            raise MessageException("You don't have permission to access this contest", 
                                   status.HTTP_403_FORBIDDEN)
        return contest_helper(contest)
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def contest_slug_is_unique(slug: str, is_update = False) -> bool | MessageException:
    """
    Check if the slug is unique
    :param slug: str
    :return: bool
    """
    try:
        contest = await contest_collection.find_one({"slug": slug})
        if contest and not is_update:
            return MessageException("The title already exists.",
                                    status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when check slug",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def retrieve_contest_detail(id: str, clerk_user_id: str) -> dict | MessageException:
    """
    Retrieve a contest with a matching contest_id (id),
    including exams with available for clerk_user_id.
    :param id: str
    :return: list
    """
    try:
        contest = await retrieve_contest(id, clerk_user_id)
        if isinstance(contest, MessageException):
            return contest
        
        all_exam = await retrieve_exams_by_contest(contest["id"])
        if isinstance(all_exam, MessageException):
            return all_exam
        
        if not all_exam:
            contest["available_exam"] = None
            contest["retake_id"] = None
            contest["exams"] = []
            return contest
            
        all_exam_detail = []
        retake_info = []
        for exam in all_exam:

            exam_id = exam["id"]
            exam_problems = await retrieve_by_exam_id(exam_id)

            exam["problems"] = exam_problems
            all_exam_detail.append(exam)

            retakes = await retrieve_retakes_by_user_exam_id(clerk_user_id, exam_id)
            retake_info.extend(retakes)

        contest["exams"] = all_exam_detail
        # Exist retake
        if retake_info: 
            newest_retake = max(retake_info, key=lambda x: x["created_at"])
            newest_exam_id = newest_retake["exam_id"]
            contest["available_exam"] = next((exam for exam in all_exam_detail if exam["id"] == newest_exam_id), None)
            contest["retake_id"] = newest_retake["id"]
        # No retake
        else: 
            contest["retake_id"] = None
            contest["available_exam"] = all_exam_detail[0]

        return contest
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when retrieve contest detail",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def update_contest(id: str, data: dict) -> bool:
    """
    Update a contest with a matching ID
    :param id: str
    :param data: dict
    :return: bool
    """
    try:
        if len(data) < 1:
            raise MessageException("No data to update", 
                                   status.HTTP_400_BAD_REQUEST)
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        updated_contest = await contest_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_contest.modified_count == 0:
            raise MessageException("Update contest failed", 
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when update contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def delete_contest(id: str) -> bool:
    """
    Delete a contest with a matching ID
    :param id: str
    :return: bool
    """
    try:
        contest = await contest_collection.find_one({"_id": ObjectId(id)})
        if not contest:
            raise MessageException("Contest not found", 
                                   status.HTTP_404_NOT_FOUND)
        
        all_exam = await exam_collection.find({"contest_id": ObjectId(id)}).to_list(length=None)
        if len(all_exam) > 0:
            await delete_all_by_contest_id(id)

        deleted_contest = await contest_collection.delete_one({"_id": ObjectId(id)})
        if deleted_contest.deleted_count == 0:
            raise MessageException("Delete contest failed", 
                                   status.HTTP_400_BAD_REQUEST)
        return True
    except MessageException as e:
        return e
    except:
        logger.error(f"{traceback.format_exc()}")
        return MessageException("Error when delete contest",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)


async def submission_result(submitted_problems: List[SubmittedProblem], error_dict: bool = False):
    try:
        TOTAL_SCORE = 0
        MAX_SCORE = 0
        TOTAL_PASSED = 0
        if submitted_problems is None:
            submitted_results = None
        else:
            submitted_results = []
            for submitted_problem in submitted_problems:
                problem_id = submitted_problem.problem_id
                problem_info = await retrieve_problem(problem_id, full_return=True)
                if isinstance(problem_info, MessageException):
                    if error_dict:
                        return {
                            "status_code": problem_info.status_code,
                            "message": problem_info.message
                        }
                    return problem_info
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

                for choice in problem_info["choices"]:
                    choice["choice_id"] = str(choice["choice_id"])
                
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
                    ).model_dump()
                )
    except MessageException as e:
        if error_dict:
            return {
                "status_code": e.status_code,
                "message": e.message
            }
        return e
    except:
        logger.error(f"Error when compute the result of the submission: {e}")
        if error_dict:
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error when compute the result of the submission."
            }
        return MessageException("Error when compute the result of the submission.",
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return {
            "submitted_results": submitted_results,
            "total_score": TOTAL_SCORE,
            "max_score": MAX_SCORE,
            "total_passed": TOTAL_PASSED
        }