# audit_logger.py
import os
import logging
from logging.handlers import TimedRotatingFileHandler

# Set audit log directory
AUDIT_LOG_DIR = r"C:\Users\chasp\Documents\WORK\SKILL SCANNER\SKSC_Prototype\AuditTrail"
os.makedirs(AUDIT_LOG_DIR, exist_ok=True)

# === General log (human readable)
log_file = os.path.join(AUDIT_LOG_DIR, "LOGFILE.log")
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

file_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


