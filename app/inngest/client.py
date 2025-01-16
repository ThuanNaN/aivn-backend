import logging
import inngest
from app.core.config import settings

logger = logging.getLogger("uvicorn.inngest")
logger.setLevel(logging.DEBUG)

inngest_client = inngest.Inngest(
    app_id=settings.PROJECT_NAME,
    env=settings.ENV_TYPE,
    is_production=settings.ENV_TYPE == "production",
    signing_key=settings.INNGEST_SIGNING_KEY,
    event_key=settings.INNGEST_EVENT_KEY,
    logger=logger
)
