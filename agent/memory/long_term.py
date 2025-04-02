"""
Long Term Memory Module
Stores successful interaction patterns and learning data in the local file system.

This module performs the following tasks:
1. Stores successful interaction patterns
2. Manages pattern-based learning data
3. Stores statistics and analysis data
4. Provides pattern search and utilization
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
import os
from utils.logger import Logger
from utils.validators import Validator

class LongTermMemory:
    """
    Long Term Memory Class
    Stores successful interaction patterns and learning data in the local file system.
    
    This class implements a two-level storage system:
    1. In-memory cache for fast access to frequently used patterns
    2. File system storage for persistent data
    
    The data is organized as follows:
    - Patterns: Individual JSON files in data/memory/patterns/
    - Statistics: Single JSON file in data/memory/stats/pattern_stats.json
    """
    
    def __init__(self, storage_path: str = "data/memory"):
        """
        Initialize the Long Term Memory system.
        
        Args:
            storage_path (str): Base directory for storing memory data
                              Default: "data/memory"
        """
        # Initialize utility classes for logging and validation
        self.logger = Logger(__name__)
        self.validator = Validator()
        
        # Set up storage paths
        self.storage_path = storage_path
        self.patterns_path = os.path.join(storage_path, "patterns")  # Directory for pattern files
        self.stats_path = os.path.join(storage_path, "stats")        # Directory for statistics
        
        # Initialize storage directories
        self._initialize_storage()
        
        # Initialize in-memory caches for performance optimization
        self.patterns_cache = {}  # Cache for pattern data
        self.stats_cache = {}     # Cache for statistics
        
        # Limit cache size to prevent memory issues
        self.max_cache_size = 1000

    def _initialize_storage(self) -> None:
        """
        Initialize storage directories.
        Creates necessary directories if they don't exist.
        """
        try:
            # Create required directories
            for path in [self.patterns_path, self.stats_path]:
                os.makedirs(path, exist_ok=True)
                
            self.logger.log_info("Local storage initialized successfully")
            
        except Exception as e:
            self.logger.log_error(f"Error initializing storage: {str(e)}")

    def save_pattern(self, pattern_key: str, pattern_data: Dict) -> bool:
        """
        Save a successful interaction pattern.
        
        This method:
        1. Validates the pattern data
        2. Saves it to a JSON file
        3. Updates the in-memory cache
        4. Updates pattern statistics
        
        Args:
            pattern_key (str): Unique identifier for the pattern
            pattern_data (Dict): Pattern data to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Validate pattern data format
            if not self.validator.validate_pattern(pattern_data):
                raise ValueError("Invalid pattern data format")
                
            # Save pattern to file
            file_path = os.path.join(self.patterns_path, f"{pattern_key}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, ensure_ascii=False, indent=2)
                
            # Update cache with size limit
            if len(self.patterns_cache) >= self.max_cache_size:
                self.patterns_cache.pop(next(iter(self.patterns_cache)))
            self.patterns_cache[pattern_key] = pattern_data
            
            # Update pattern statistics
            self._update_pattern_stats(pattern_key, pattern_data)
            
            self.logger.log_info(f"Pattern saved successfully: {pattern_key}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error saving pattern: {str(e)}")
            return False

    def get_pattern(self, pattern_key: str) -> Optional[Dict]:
        """
        Retrieve a pattern by its key.
        
        This method implements a two-level lookup:
        1. First checks the in-memory cache
        2. If not found, loads from file system
        
        Args:
            pattern_key (str): Unique identifier for the pattern
            
        Returns:
            Optional[Dict]: Pattern data if found, None otherwise
        """
        try:
            # Check cache first
            if pattern_key in self.patterns_cache:
                return self.patterns_cache[pattern_key]
                
            # Load from file if not in cache
            file_path = os.path.join(self.patterns_path, f"{pattern_key}.json")
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                pattern = json.load(f)
                
            # Update cache with size limit
            if len(self.patterns_cache) >= self.max_cache_size:
                self.patterns_cache.pop(next(iter(self.patterns_cache)))
            self.patterns_cache[pattern_key] = pattern
            return pattern
            
        except Exception as e:
            self.logger.log_error(f"Error retrieving pattern: {str(e)}")
            return None

    def search_patterns(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for patterns matching the query.
        
        This method implements a two-level search:
        1. First searches in the cache
        2. Then searches in the file system
        
        Args:
            query (str): Search term
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching patterns
        """
        try:
            results = []
            query = query.lower()
            
            # Search in cache
            for pattern_key, pattern in self.patterns_cache.items():
                if query in str(pattern).lower():
                    results.append(pattern)
                    if len(results) >= limit:
                        return results
            
            # Search in file system
            for filename in os.listdir(self.patterns_path):
                if not filename.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.patterns_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    pattern = json.load(f)
                    
                if query in str(pattern).lower():
                    results.append(pattern)
                    if len(results) >= limit:
                        break
                    
            return results
            
        except Exception as e:
            self.logger.log_error(f"Error searching patterns: {str(e)}")
            return []

    def _update_pattern_stats(self, pattern_key: str, pattern_data: Dict) -> None:
        """
        Update pattern statistics.
        
        This method:
        1. Loads existing statistics
        2. Updates pattern counts
        3. Saves updated statistics
        
        Args:
            pattern_key (str): Pattern identifier
            pattern_data (Dict): Pattern data
        """
        try:
            stats_file = os.path.join(self.stats_path, "pattern_stats.json")
            
            # Load existing statistics
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {
                    'total_patterns': 0,
                    'pattern_counts': {},
                    'last_updated': None
                }
            
            # Update statistics
            stats['total_patterns'] += 1
            stats['pattern_counts'][pattern_key] = pattern_data.get('count', 0)
            stats['last_updated'] = datetime.now().isoformat()
            
            # Save updated statistics
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
            # Update cache
            self.stats_cache = stats
            
        except Exception as e:
            self.logger.log_error(f"Error updating pattern statistics: {str(e)}")

    def get_pattern_stats(self) -> Dict:
        """
        Retrieve pattern statistics.
        
        This method implements a two-level lookup:
        1. First checks the cache
        2. If not found, loads from file
        
        Returns:
            Dict: Statistics data including total patterns and usage counts
        """
        try:
            # Check cache first
            if self.stats_cache:
                return self.stats_cache
                
            # Load from file if not in cache
            stats_file = os.path.join(self.stats_path, "pattern_stats.json")
            if not os.path.exists(stats_file):
                return {
                    'total_patterns': 0,
                    'pattern_counts': {},
                    'last_updated': None
                }
                
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                
            # Update cache
            self.stats_cache = stats
            return stats
            
        except Exception as e:
            self.logger.log_error(f"Error retrieving pattern statistics: {str(e)}")
            return {}

    def clear_cache(self) -> None:
        """
        Clear the in-memory caches.
        This method is useful for:
        1. Freeing up memory
        2. Ensuring fresh data on next access
        3. Debugging purposes
        """
        self.patterns_cache.clear()
        self.stats_cache.clear()
        self.logger.log_info("Memory cache cleared successfully") 