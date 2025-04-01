# utils/validators.py
from typing import Dict, List

class Validator:
    """Shared validation interface"""
    @staticmethod
    def validate_document(document: Dict) -> bool:
        """Validate document structure"""
        pass

    @staticmethod
    def validate_task(task: Dict) -> bool:
        """Validate task structure"""
        pass

    @staticmethod
    def validate_search_result(result: Dict) -> bool:
        """Validate search result structure"""
        pass