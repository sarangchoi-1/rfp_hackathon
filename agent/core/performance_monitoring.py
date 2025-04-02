from typing import Dict, List
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    에이전트의 성능을 모니터링하고 측정하는 클래스
    """
    
    def __init__(self):
        self.metrics: List[Dict] = []
        self.active_operations: Dict[str, float] = {}
        
    def start_operation(self, operation_name: str):
        """
        작업 시작 시간을 기록합니다.
        
        Args:
            operation_name (str): 작업의 이름
        """
        self.active_operations[operation_name] = time.time()
        logger.debug(f"작업 시작: {operation_name}")
        
    def end_operation(self, operation_name: str):
        """
        작업 종료 시간을 기록하고 실행 시간을 계산합니다.
        
        Args:
            operation_name (str): 작업의 이름
        """
        if operation_name in self.active_operations:
            start_time = self.active_operations[operation_name]
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 메트릭 기록
            self.record_metric(operation_name, execution_time)
            
            # 활성 작업에서 제거
            del self.active_operations[operation_name]
            logger.debug(f"작업 종료: {operation_name} (소요 시간: {execution_time:.2f}초)")
        else:
            logger.warning(f"시작되지 않은 작업 종료 시도: {operation_name}")
        
    def record_metric(self, function_name: str, execution_time: float):
        """
        성능 메트릭을 기록합니다.
        
        Args:
            function_name (str): 측정된 함수의 이름
            execution_time (float): 실행 시간 (초)
        """
        metric = {
            "function": function_name,
            "execution_time": execution_time,
            "timestamp": time.time()
        }
        self.metrics.append(metric)
        logger.debug(f"성능 메트릭 기록: {metric}")
        
    def get_metrics(self) -> List[Dict]:
        """
        기록된 모든 성능 메트릭을 반환합니다.
        
        Returns:
            List[Dict]: 성능 메트릭 리스트
        """
        return self.metrics
    
    def clear_metrics(self):
        """기록된 모든 성능 메트릭을 초기화합니다."""
        self.metrics = []
        self.active_operations.clear()

def measure_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        performance_metrics = {
            "function": func.__name__,
            "execution_time": end_time - start_time,
            "timestamp": time.time()
        }
        
        # Log or store metrics
        return result, performance_metrics
    return wrapper