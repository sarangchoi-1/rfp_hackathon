from typing import Dict
import time
from functools import wraps

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