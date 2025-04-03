from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class CacheSystem:
    def __init__(self, ttl: int = 3600):  # Default TTL: 1 hour
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}
        
    def _create_hash_key(self, value: Any) -> str:
        """Create a consistent hash key for any input value."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        return hashlib.md5(str(value).encode()).hexdigest()

    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """Get cached value using prefix and parameters."""
        key = f"{prefix}_{self._create_hash_key(kwargs)}"
        if key in self.cache:
            # Check if cache entry has expired
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                logger.debug(f"Cache hit for key: {key}")
                return self.cache[key]
            else:
                # Remove expired entry
                self.remove(key)
        return None
        
    def set(self, prefix: str, value: Any, **kwargs) -> None:
        """Set cache value using prefix and parameters."""
        key = f"{prefix}_{self._create_hash_key(kwargs)}"
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        logger.debug(f"Cached value for key: {key}")
        
    def remove(self, key: str) -> None:
        """Remove a cache entry."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        
    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from prefix and parameters."""
        # Sort kwargs to ensure consistent key generation
        sorted_items = sorted(kwargs.items())
        key_parts = [str(k) + ":" + str(v) for k, v in sorted_items]
        return f"{prefix}_{'-'.join(key_parts)}"