import logging
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
LOG_DIR = os.path.abspath(LOG_DIR)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 'debug.log')

logger = logging.getLogger('7DaysToBackup')
logger.setLevel(logging.DEBUG)

# Avoid adding multiple handlers if module imported multiple times
if not logger.handlers:
    fh = logging.FileHandler(LOG_PATH, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # also add a minimal stream handler for console during development
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
