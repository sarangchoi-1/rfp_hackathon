"""
단기 메모리 모듈 (Short-term Memory Module)
최근 상호작용과 임시 컨텍스트를 관리합니다.

이 모듈은 다음과 같은 작업을 수행합니다:
1. 최근 상호작용 저장 (메모리 내)
2. 임시 컨텍스트 관리
3. 작업 히스토리 추적
4. 성공적인 상호작용 패턴 학습
"""

from typing import List, Dict
from datetime import datetime
from utils.logger import Logger
from utils.validators import Validator
from utils.exceptions import MemoryError
from .long_term import LongTermMemory

class ShortTermMemory:
    """
    단기 메모리 클래스
    최근 상호작용과 임시 컨텍스트를 관리합니다.
    """
    
    def __init__(self):
        # 기본 유틸리티 초기화
        self.logger = Logger(__name__)
        self.validator = Validator()
        
        # 장기 메모리 초기화 (학습 데이터 저장용)
        self.long_term = LongTermMemory()
        
        # 메모리 초기화
        self.conversation_history = []  # 대화 기록
        self.recent_tasks = []          # 최근 작업 목록
        self.current_context = {}       # 현재 컨텍스트
        self.successful_patterns = {}   # 성공적인 상호작용 패턴
        
        # 성능 최적화를 위한 설정
        self.max_history = 20           # 저장할 최대 상호작용 수
        self.pattern_threshold = 3      # 패턴으로 인정할 최소 반복 횟수

    def add_interaction(self, interaction: Dict) -> bool:
        """
        최근 상호작용 저장 및 패턴 학습
        
        Args:
            interaction (Dict): 상호작용 정보
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            if not self.validator.validate_interaction(interaction):
                raise MemoryError("유효하지 않은 상호작용 형식")
            
            # 상호작용에 타임스탬프 추가
            interaction_data = {
                'timestamp': datetime.now().isoformat(),
                'interaction': interaction
            }
            
            # 대화 기록에 추가 (성능 최적화)
            self.conversation_history.append(interaction_data)
            if len(self.conversation_history) > self.max_history:
                self.conversation_history.pop(0)
            
            # 현재 컨텍스트 업데이트
            self._update_current_context(interaction)
            
            # 성공적인 상호작용 패턴 학습
            if interaction.get('success', False):
                self._learn_pattern(interaction)
            
            self.logger.log_info("상호작용이 단기 메모리에 추가되었습니다")
            return True
            
        except Exception as e:
            self.logger.log_error(f"상호작용 추가 중 오류 발생: {str(e)}")
            return False

    def _learn_pattern(self, interaction: Dict) -> None:
        """
        성공적인 상호작용 패턴 학습
        
        Args:
            interaction (Dict): 성공적인 상호작용
        """
        try:
            # 패턴 키 생성 (작업 유형 + 주요 키워드)
            pattern_key = f"{interaction.get('task_type', '')}_{interaction.get('keywords', '')}"
            
            # 패턴 카운트 증가
            if pattern_key in self.successful_patterns:
                self.successful_patterns[pattern_key]['count'] += 1
            else:
                self.successful_patterns[pattern_key] = {
                    'count': 1,
                    'last_success': datetime.now().isoformat(),
                    'example': interaction
                }
            
            # 충분히 반복된 패턴은 장기 메모리에 저장
            if self.successful_patterns[pattern_key]['count'] >= self.pattern_threshold:
                self.long_term.save_pattern(pattern_key, self.successful_patterns[pattern_key])
                
        except Exception as e:
            self.logger.log_error(f"패턴 학습 중 오류 발생: {str(e)}")

    def get_recent_context(self) -> Dict:
        """
        최근 대화 컨텍스트 조회
        
        Returns:
            Dict: 컨텍스트 정보
        """
        return {
            'history': self.conversation_history,
            'current_context': self.current_context,
            'recent_tasks': self.recent_tasks,
            'successful_patterns': self.successful_patterns,
            'last_updated': datetime.now().isoformat()
        }

    def update_current_context(self, context_data: Dict) -> bool:
        """
        현재 컨텍스트 업데이트
        
        Args:
            context_data (Dict): 컨텍스트 데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            self.current_context.update(context_data)
            self.current_context['last_updated'] = datetime.now().isoformat()
            return True
        except Exception as e:
            self.logger.log_error(f"컨텍스트 업데이트 중 오류 발생: {str(e)}")
            return False

    def add_recent_task(self, task: Dict) -> bool:
        """
        최근 작업 추가
        
        Args:
            task (Dict): 작업 정보
            
        Returns:
            bool: 추가 성공 여부
        """
        try:
            if not self.validator.validate_task(task):
                raise MemoryError("유효하지 않은 작업 형식")
                
            task_data = {
                'timestamp': datetime.now().isoformat(),
                'task': task
            }
            
            self.recent_tasks.append(task_data)
            
            # 최대 작업 수 제한
            if len(self.recent_tasks) > self.max_history:
                self.recent_tasks.pop(0)
                
            return True
            
        except Exception as e:
            self.logger.log_error(f"최근 작업 추가 중 오류 발생: {str(e)}")
            return False

    def clear_old_data(self) -> None:
        """오래된 데이터 정리"""
        try:
            current_time = datetime.now()
            
            # 오래된 상호작용 제거
            self.conversation_history = [
                interaction for interaction in self.conversation_history
                if (current_time - datetime.fromisoformat(interaction['timestamp'])).total_seconds() < 3600
            ]
            
            # 오래된 작업 제거
            self.recent_tasks = [
                task for task in self.recent_tasks
                if (current_time - datetime.fromisoformat(task['timestamp'])).total_seconds() < 3600
            ]
            
            # 오래된 패턴 제거
            self.successful_patterns = {
                key: pattern for key, pattern in self.successful_patterns.items()
                if (current_time - datetime.fromisoformat(pattern['last_success'])).total_seconds() < 86400  # 24시간
            }
            
            self.logger.log_info("단기 메모리에서 오래된 데이터가 정리되었습니다")
            
        except Exception as e:
            self.logger.log_error(f"오래된 데이터 정리 중 오류 발생: {str(e)}")

    def _update_current_context(self, interaction: Dict) -> None:
        """
        현재 컨텍스트 업데이트 (내부 메서드)
        
        Args:
            interaction (Dict): 상호작용 정보
        """
        try:
            # 상호작용에서 컨텍스트 정보 추출
            if 'context' in interaction:
                self.current_context.update(interaction['context'])
                self.current_context['last_updated'] = datetime.now().isoformat()
        except Exception as e:
            self.logger.log_error(f"컨텍스트 업데이트 중 오류 발생: {str(e)}") 