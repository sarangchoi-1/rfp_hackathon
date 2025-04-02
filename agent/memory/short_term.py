"""
Short-term Memory Module
Handles recent interactions and temporary context.
"""

from typing import List, Dict
from datetime import datetime
from utils.logger import Logger
from utils.validators import Validator
from utils.exceptions import MemoryError

class ShortTermMemory:
    def __init__(self):
        self.logger = Logger(__name__)
        self.validator = Validator()
        self.conversation_history = []
        self.recent_tasks = []
        self.current_context = {}
        self.max_history = 10  # Maximum number of interactions to keep

    def add_interaction(self, interaction: Dict):
        """Store recent interaction"""
        try:
            if not self.validator.validate_interaction(interaction):
                raise MemoryError("Invalid interaction format")
            
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'interaction': interaction
            })
            if len(self.conversation_history) > self.max_history:
                self.conversation_history.pop(0)
            
            self.logger.log_info(f"Added interaction to short-term memory")
        except Exception as e:
            self.logger.log_error(f"Error adding interaction: {str(e)}")
            raise

    def get_recent_context(self) -> Dict:
        """Get recent conversation context"""
        return {
            'history': self.conversation_history,
            'current_context': self.current_context
        }

    def clear_old_data(self):
        """Remove outdated information"""
        try:
            current_time = datetime.now()
            self.conversation_history = [
                interaction for interaction in self.conversation_history
                if (current_time - interaction['timestamp']).total_seconds() < 3600  # Keep last hour
            ]
            self.logger.log_info("Cleared old data from short-term memory")
        except Exception as e:
            self.logger.log_error(f"Error clearing old data: {str(e)}")
            raise 