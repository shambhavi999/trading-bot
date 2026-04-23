import json
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs as structured JSON."""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    """Configures global logging with both file (JSON) and stream (human-readable) handlers."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return

    # File Handler (JSON formatting, rotating at 5MB, keeping 3 backups)
    file_handler = RotatingFileHandler(
        "logs/trading_bot.log", maxBytes=5*1024*1024, backupCount=3
    )
    file_handler.setFormatter(JSONFormatter())
    
    # Stream Handler (Human readable)
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(stream_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

def get_logger(name: str):
    """Helper to get a named logger after setup."""
    return logging.getLogger(name)

# Ensure logging is setup when module is imported
setup_logging()
