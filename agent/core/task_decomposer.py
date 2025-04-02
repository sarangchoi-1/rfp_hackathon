"""
Task Decomposition Module
Handles breaking down user requests into structured tasks.
"""

from typing import List, Dict
from utils.logger import Logger
from utils.validators import Validator
from utils.exceptions import TaskError
from ..memory.short_term import ShortTermMemory
from ..memory.long_term import LongTermMemory
from ..memory.working import WorkingMemory
import uuid
import re

class TaskDecomposer:
    def __init__(self):
        self.logger = Logger(__name__)
        self.validator = Validator()
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        self.working_memory = WorkingMemory()
        
        # Define task types and their priorities
        self.task_types = {
            'purpose': {
                'priority': 1,
                'keywords': ['목적', '목표', '배경', '필요성', 'why', 'purpose', 'objective'],
                'dependencies': []
            },
            'scope': {
                'priority': 2,
                'keywords': ['범위', '규모', '기간', '대상', 'scope', 'scale', 'timeline'],
                'dependencies': ['purpose']
            },
            'case': {
                'priority': 3,
                'keywords': ['사례', '예시', '참고', '벤치마크', 'case', 'example', 'reference'],
                'dependencies': ['scope']
            },
            'evaluation': {
                'priority': 4,
                'keywords': ['평가', '기준', '지표', '점수', 'evaluation', 'criteria', 'metrics'],
                'dependencies': ['scope', 'case']
            }
        }

    def decompose_request(self, user_request: str) -> List[Dict]:
        """
        Decompose user request into structured tasks
        Returns: List of task dictionaries with:
            - task_id: str
            - task_type: str (purpose/scope/case/evaluation)
            - description: str
            - priority: int
            - dependencies: List[str]
        """
        try:
            # Get context from memory
            context = self.short_term_memory.get_recent_context()
            
            # Initialize tasks list
            tasks = []
            
            # Generate tasks for each type
            for task_type, config in self.task_types.items():
                task_id = str(uuid.uuid4())[:8]
                description = self._generate_task_description(user_request, task_type, config['keywords'])
                
                task = {
                    'task_id': task_id,
                    'task_type': task_type,
                    'description': description,
                    'priority': config['priority'],
                    'dependencies': self._get_dependencies(task_id, task_type, tasks)
                }
                tasks.append(task)
            
            # Adjust priorities based on context
            tasks = self._adjust_priorities(tasks, context)
            
            # Validate tasks
            if not self.validate_tasks(tasks):
                raise TaskError("Invalid task structure")
            
            # Store in working memory
            self.working_memory.set_current_task({'tasks': tasks, 'request': user_request})
            
            self.logger.log_info(f"Successfully decomposed request into {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            self.logger.log_error(f"Error decomposing request: {str(e)}")
            raise

    def _generate_task_description(self, request: str, task_type: str, keywords: List[str]) -> str:
        """Generate task description based on request and type"""
        try:
            # Base prompts for each task type
            prompts = {
                'purpose': "RFP의 목적과 배경을 파악하여 정리",
                'scope': "프로젝트의 범위와 규모를 정의",
                'case': "관련 사례와 참고 자료 조사",
                'evaluation': "평가 기준과 지표 설정"
            }
            
            # Extract relevant part from request using keywords
            relevant_parts = []
            for keyword in keywords:
                pattern = f"[^.]*{keyword}[^.]*\\."
                matches = re.findall(pattern, request, re.IGNORECASE)
                relevant_parts.extend(matches)
            
            # Combine base prompt with relevant parts
            description = f"{prompts[task_type]}"
            if relevant_parts:
                description += f" (관련 내용: {' '.join(relevant_parts)})"
            
            return description.strip()
            
        except Exception as e:
            self.logger.log_error(f"Error generating task description: {str(e)}")
            return prompts[task_type]  # Fallback to base prompt

    def _get_dependencies(self, task_id: str, task_type: str, existing_tasks: List[Dict]) -> List[str]:
        """Get task dependencies based on type"""
        try:
            dependencies = []
            required_types = self.task_types[task_type]['dependencies']
            
            for task in existing_tasks:
                if task['task_type'] in required_types:
                    dependencies.append(task['task_id'])
            
            return dependencies
            
        except Exception as e:
            self.logger.log_error(f"Error getting dependencies: {str(e)}")
            return []

    def _adjust_priorities(self, tasks: List[Dict], context: Dict) -> List[Dict]:
        """Adjust task priorities based on context"""
        try:
            # Get historical performance
            history = self.long_term_memory.get_task_history()
            
            for task in tasks:
                base_priority = task['priority']
                
                # Adjust based on historical success rate
                if history and task['task_type'] in history:
                    success_rate = history[task['task_type']].get('success_rate', 1.0)
                    task['priority'] = int(base_priority / success_rate)
                
                # Adjust based on dependencies
                if task['dependencies']:
                    task['priority'] += len(task['dependencies'])
            
            # Sort tasks by priority
            tasks.sort(key=lambda x: x['priority'])
            return tasks
            
        except Exception as e:
            self.logger.log_error(f"Error adjusting priorities: {str(e)}")
            return tasks

    def validate_tasks(self, tasks: List[Dict]) -> bool:
        """Validate task structure and completeness"""
        try:
            if not isinstance(tasks, list):
                return False
            
            task_ids = set()
            for task in tasks:
                if not self.validator.validate_task(task):
                    return False
                    
                # Check for duplicate task IDs
                if task['task_id'] in task_ids:
                    return False
                task_ids.add(task['task_id'])
                
                # Check task type validity
                if task['task_type'] not in self.task_types:
                    return False
                
                # Check dependency validity
                for dep_id in task['dependencies']:
                    if dep_id not in task_ids:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Error validating tasks: {str(e)}")
            return False 