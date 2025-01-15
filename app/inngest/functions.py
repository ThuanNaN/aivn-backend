from datetime import datetime
import inngest
from app.inngest.client import inngest_client
from app.api.v1.controllers.certificate import (
    add_certificate
)

@inngest_client.create_function(
    fn_id="create-certificate",
    trigger=inngest.TriggerEvent(event="contest/certificate"),
)
async def create_certificate(ctx: inngest.Context,
                             step: inngest.Step
                             ) -> dict:
    cer_data = ctx.event.data
    cer_data["created_at"] = datetime.fromisoformat(cer_data["created_at"])

    create_cer = await step.run(
        "step-create-certificate", 
        lambda: add_certificate(cer_data)
    )
    return create_cer

inngest_functions = [
    create_certificate,
]