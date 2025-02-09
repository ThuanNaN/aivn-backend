from typing import List
from datetime import datetime
from app.core.config import settings
import resend
import inngest
from app.inngest.client import inngest_client
from app.schemas.enum_category import CertificateEnum
from app.core.config import settings
from datetime import datetime, UTC, timedelta
from app.utils import Logger, generate_id
from fastapi import status
from app.schemas.certificate import CertificateDB
from app.schemas.submission import (
    UpdateSubmissionDB
)
from app.schemas.submission import (
    SubmittedProblem,
    SubmittedResult,
    UpdateSubmissionDB
)
from app.api.v1.controllers.certificate import (
    add_certificate
)
from app.api.v1.controllers.submission import (
    add_submission,
    update_submission,
    retrieve_submission_by_id_user_retake,
    retrieve_draft_submission,
    delete_draft_submission
)
from app.api.v1.controllers.certificate import (
    retrieve_certificate_by_validation_id
)
from app.api.v1.controllers.contest import submission_result
logger = Logger("inngest/functions", log_file="inngest.log")


resend.api_key = settings.RESEND_API_KEY
dev_email = "onboarding@resend.dev"
prod_email = "AIVietnam@aivnlearning.com"
email_address = prod_email if settings.ENV_TYPE == "production" else dev_email

with open("./app/static/new-certificate.html") as f:
    base_email_html = f.read()


@inngest_client.create_function(
    fn_id="create-certificate",
    trigger=inngest.TriggerEvent(event="contest/certificate"),
    retries=1,
)
async def create_certificate(ctx: inngest.Context, step: inngest.Step) -> dict:
    certificate_info = ctx.event.data["certificate_info"]
    certificate_info["created_at"] = datetime.fromisoformat(certificate_info["created_at"])
    created_certificate = await step.run(
        "step-create-certificate", 
        lambda: add_certificate(certificate_info)
    )
    if created_certificate.get("status_code") == status.HTTP_500_INTERNAL_SERVER_ERROR:
        return "Error when create certificate"
    
    await step.send_event(
        "notify-certificate",
        events=inngest.Event(
            name="email/certificate",
            id=f"{certificate_info['validation_id']}",
            data=ctx.event.data
        )
    )
    return created_certificate


@inngest_client.create_function(
    fn_id="email-certificate",
    trigger=inngest.TriggerEvent(event="email/certificate"),
    retries=1,
)
async def email_certificate(ctx: inngest.Context, step: inngest.Step) -> dict:
    user_info = ctx.event.data["user_info"]
    certificate_info = ctx.event.data["certificate_info"]
    certificate_name = CertificateEnum.get_certificate_name(certificate_info["template"])
    certificate_url = f"{settings.FRONTEND_URL}/verification/accomplishments/{certificate_info['validation_id']}"
    email_html = base_email_html.replace(
        "###fullname###", user_info["fullname"]    
    ).replace(
        "###certificate_name###", certificate_name
    ).replace(
        "###certificate_url###", certificate_url
    )
    
    params: resend.Emails.SendParams = {
        "from": email_address,
        "to": [user_info["email"]],
        "subject": "Congratulations! You recently gained a Certificate!",
        "html": email_html,
    }
    sent_email = await step.run(
        "step-send-email",
        lambda: resend.Emails.send(params)
    )
    return sent_email



@inngest_client.create_function(
    fn_id="create-pseudo-submission",
    trigger=inngest.TriggerEvent(event="contest/submission"),
    retries=1,
)
async def create_pseudo_submission(ctx: inngest.Context, step: inngest.Step) -> dict:
    submission_data = ctx.event.data["submission_info"]
    submission_data["created_at"] = datetime.fromisoformat(submission_data["created_at"])
    create_submission = await step.run(
        "step-pseudo-submission",
        lambda: add_submission(submission_data)
    )
    if create_submission.get("status_code") == status.HTTP_500_INTERNAL_SERVER_ERROR:
        return "Error when create submission"
    
    await step.send_event(
        "check-timeout-submission",
        events=inngest.Event(
            name="exam/submit",
            id=create_submission["id"],
            data={
                "submission_info": create_submission,
                "exam_info": ctx.event.data["exam_info"],
                "contest_info": ctx.event.data["contest_info"],
                "user_info": ctx.event.data["user_info"]
            }
        )
    )
    return create_submission


@inngest_client.create_function(
    fn_id="timeout-submit",
    retries=1,
    trigger=inngest.TriggerEvent(event="exam/submit"),
    cancel=[
        inngest.Cancel(event="exam/submited", 
                       if_exp="async.data['submission_info']['id'] == event.data['submission_info']['id']")
    ]
)
async def timeout_submit(ctx: inngest.Context, step: inngest.Step) -> dict:
    # Step 0: Wait for the exam duration
    exam_info = ctx.event.data["exam_info"]
    await step.sleep(
        "wait-to-submit",
        timedelta(minutes=exam_info["duration"], seconds=5)
    )
    # Retrieve the draft submission
    submission_info = ctx.event.data["submission_info"]
    retrieve_input = {
        "exam_id": submission_info["exam_id"],
        "retake_id": submission_info["retake_id"],
        "clerk_user_id": submission_info["clerk_user_id"],
        "error_dict": True
    }
    draft_submission = await step.run(
        "step-retrieve-draft-submission",
        lambda: retrieve_draft_submission(**retrieve_input)
    )
    if draft_submission.get("status_code") in [status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                               status.HTTP_404_NOT_FOUND]:
        return draft_submission.get("message")
    
    # Step 1: Compute the result of the submission
    submitted_problems: List[SubmittedProblem] = [SubmittedProblem(**sub) for sub 
                                                  in draft_submission["submitted_problems"]]
    exam_results = await step.run(
        "step-exam-result",
        lambda: submission_result(submitted_problems)
    )
    if exam_results.get("status_code") in [status.HTTP_500_INTERNAL_SERVER_ERROR,
                                          status.HTTP_404_NOT_FOUND]:
        return exam_results.get("message")

    # Step 2: Retrieve pseudo submission
    pseudo_submission = await step.run(
        "step-retrieve-pseudo-submission",
        lambda: retrieve_submission_by_id_user_retake(
            **retrieve_input,
            check_none=False
        )
    )
    if pseudo_submission.get("status_code") in [status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                status.HTTP_404_NOT_FOUND]:
        return pseudo_submission.get("message")
    
    # Step 3: Update the submission
    upsert_submission_data = UpdateSubmissionDB(
        retake_id=submission_info["retake_id"],
        submitted_problems=[SubmittedResult(**prob) for prob in exam_results["submitted_results"]],
        total_score=exam_results["total_score"],
        max_score=exam_results["max_score"],
        total_problems=len(draft_submission["submitted_problems"]),
        total_problems_passed=exam_results["total_passed"],
        created_at=datetime.now(UTC)
    ).model_dump()

    upsert_submission = await step.run(
        "step-update-submission",
        lambda: update_submission(
            pseudo_submission["id"],
            upsert_submission_data
        )
    )
    if "message" in upsert_submission:
        return upsert_submission["message"]

    # Step 4: Check if the user passed the exam
    contest_info = ctx.event.data["contest_info"]
    user_info = ctx.event.data["user_info"]

    if (contest_info["certificate_template"] is not None 
    and exam_results["max_score"] > 0 
    and exam_results["total_score"] / exam_results["max_score"] >= 0.5):
        validation_id = generate_id()
        # Check if validation_id is exist
        start_time = datetime.now(UTC)
        while await retrieve_certificate_by_validation_id(validation_id):
            validation_id = generate_id()
        end_time = datetime.now(UTC)
        logger.info(f"Generate validation_id in {end_time - start_time}")

        # Create a new certificate
        certificate_data = CertificateDB(
            validation_id=validation_id,
            clerk_user_id=submission_info["clerk_user_id"],
            submission_id=pseudo_submission["id"],
            result_score=f"{exam_results['total_score']}/{exam_results['max_score']}",
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
    
    # Step 5: Delete the draft submission
    await inngest_client.send(
        inngest.Event(
            name="exam/delete-draft-submission",
            id=f"delete-draft-{submission_info['id']}",
            data={
                "submission_info": submission_info,
            }
        )
    )

    upsert_submission_data["created_at"] = upsert_submission_data["created_at"].isoformat()
    return upsert_submission_data


@inngest_client.create_function(
    fn_id="delete-draft-submission",
    retries=1,
    trigger=inngest.TriggerEvent(event="exam/delete-draft-submission"),
)
async def remove_draft_submission(ctx: inngest.Context, step: inngest.Step) -> dict:
    submission_info = ctx.event.data["submission_info"]
    delete_draft_data = {
        "exam_id": submission_info["exam_id"],
        "retake_id": submission_info["retake_id"],
        "clerk_user_id": submission_info["clerk_user_id"],
        "error_dict": True
    }
    delete_draft = await step.run(
        "step-delete-draft-submission",
        lambda: delete_draft_submission(**delete_draft_data)
    )
    if delete_draft.get("status_code") in [status.HTTP_500_INTERNAL_SERVER_ERROR,
                                           status.HTTP_400_BAD_REQUEST]:
        return delete_draft.get("message")
    
    return delete_draft
