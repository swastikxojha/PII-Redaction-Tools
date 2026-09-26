import logging
import sys


def configure_logging(level: int=logging.INFO) -> logging.Logger:
    logger=logging.getLogger("pii_redaction")
    if not logger.handlers:
        handler=logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
