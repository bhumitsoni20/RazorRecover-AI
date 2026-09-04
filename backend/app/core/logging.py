import logging
import sys

from app.core.config import settings


def setup_logging():
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("razorrecover")
