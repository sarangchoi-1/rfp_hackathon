# utils/logger.py
import logging
from typing import Optional, Dict

class Logger:
    """Shared logging interface"""
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_logging()

    def setup_logging(self):
        """Configure logging format and handlers"""
        pass

    def log_request(self, request_id: str, component: str, action: str):
        """Log request details"""
        pass

    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """Log error details with context"""
        pass

    def log_performance(self, operation: str, duration: float):
        """Log performance metrics"""
        pass