import logging

from gcs.core.config import load_config
from gcs.core.logging_setup import setup_logging


def main():
    config = load_config()
    setup_logging(level=config["logging"]["level"], logfile=config["logging"]["file"])
    log = logging.getLogger(__name__)
    log.info("GCS starting")
    log.info("Input rate will be %s Hz", config["input"]["rate_hz"])


if __name__ == "__main__":
    main()