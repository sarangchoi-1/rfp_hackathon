# utils/metrics.py
from typing import Dict, List

class Metrics:
    """Shared metrics collection interface"""
    def __init__(self):
        self.metrics = {}

    def record_latency(self, operation: str, duration: float):
        """Record operation latency"""
        pass

    def record_success(self, operation: str):
        """Record successful operations"""
        pass

    def record_error(self, operation: str, error_type: str):
        """Record error occurrences"""
        pass

    def get_metrics(self) -> Dict:
        """Get collected metrics"""
        pass