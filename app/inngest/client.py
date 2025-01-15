import logging
import inngest
from app.core.config import settings

logger = logging.getLogger("uvicorn.inngest")
logger.setLevel(logging.DEBUG)

inngest_client = inngest.Inngest(app_id=settings.PROJECT_NAME, logger=logger)
