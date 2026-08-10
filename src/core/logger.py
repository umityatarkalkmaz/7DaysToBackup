import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.core.paths import get_log_dir

logger = logging.getLogger('7DaysToBackup')

_configured = False


def setup_logging() -> None:
    """Configure logging. Call once from main().

    Deliberately does nothing at import time: the previous version ran
    os.makedirs() next to __file__ while the module was being imported, which
    raises PermissionError for an installation under a read-only location
    (e.g. C:\\Program Files) and killed the app before any UI existed to report
    it. This function never raises for the same reason.
    """
    global _configured
    if _configured:
        return
    _configured = True

    logger.setLevel(logging.DEBUG if os.environ.get("SEVENDAYS_DEBUG") else logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    try:
        log_dir = get_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        fh = RotatingFileHandler(
            os.path.join(log_dir, 'debug.log'),
            maxBytes=1_000_000,
            backupCount=3,
            encoding='utf-8',
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except OSError:
        # Read-only install or unwritable home: carry on without a file log.
        pass

    # sys.stderr is None under pythonw / PyInstaller -w, where a StreamHandler
    # would raise on first emit.
    if sys.stderr is not None:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
