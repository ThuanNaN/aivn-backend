from datetime import datetime
from app.core.config import settings
import resend
import inngest
from app.inngest.client import inngest_client
from app.api.v1.controllers.certificate import (
    add_certificate
)
from app.schemas.enum_category import CertificateEnum
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY

with open("./app/static/new-certificate.html") as f:
    base_email_html = f.read()


@inngest_client.create_function(
    fn_id="create-certificate",
    trigger=inngest.TriggerEvent(event="contest/certificate"),
)
async def create_certificate(ctx: inngest.Context,
                             step: inngest.Step
                             ) -> dict:
    
    # Create certificate step
    certificate_info = ctx.event.data["certificate_info"]
    certificate_info["created_at"] = datetime.fromisoformat(certificate_info["created_at"])
    create_cer = await step.run(
        "step-create-certificate", 
        lambda: add_certificate(certificate_info)
    )

    # Send email to user for notification about certificate
    user_info = ctx.event.data["user_info"]
    certificate_name = CertificateEnum.get_certificate_name(certificate_info["template"])
    certificate_url = f"{settings.FRONTEND_URL}/verification/accomplishments/{create_cer['validation_id']}"
    email_html = base_email_html.replace(
        "###fullname###", user_info["fullname"]    
    ).replace(
        "###certificate_name###", certificate_name
    ).replace(
        "###certificate_url###", certificate_url
    )
    
    params: resend.Emails.SendParams = {
        "from": "AIVietnam@aivnlearning.com",
        "to": [user_info["email"]],
        "subject": "Congratulations! You recently gained a Certificate!",
        "html": email_html,
    }
    sent_email = await step.run(
        "step-send-email",
        lambda: resend.Emails.send(params)
    )

    return (create_cer, sent_email)



inngest_functions = [
    create_certificate,
]