import logging

from gcs.core.logging_setup import setup_logging


def main():
    setup_logging()
    log = logging.getLogger(__name__)
    log.info("GCS starting")
    log.warning("This is a test warning")


if __name__ == "__main__":
    main()