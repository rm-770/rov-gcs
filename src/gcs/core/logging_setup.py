import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(level="INFO", logfile="logs/gcs.log"):
    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(threadName)s %(name)s: %(message)s"
    )

    # Make sure the logs/ folder exists
    Path(logfile).parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=3)
    console_handler = logging.StreamHandler()

    for handler in (file_handler, console_handler):
        handler.setFormatter(fmt)
        root.addHandler(handler)

