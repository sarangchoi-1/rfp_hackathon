"""
작업 메모리 모듈 (Working Memory Module)
현재 작업의 상태와 컨텍스트를 관리합니다.

이 모듈은 다음과 같은 작업을 수행합니다:
1. 현재 작업 상태 추적
2. 작업 컨텍스트 관리
3. 작업 진행 상황 모니터링
4. 작업 간 전환 관리
"""

from typing import Dict, Optional
from datetime import datetime
from utils.logger import Logger
from utils.validators import Validator

class WorkingMemory:
    """
    작업 메모리 클래스
    현재 작업의 상태와 컨텍스트를 관리합니다.
    """
    
    def __init__(self):
        # 기본 유틸리티 초기화
        self.logger = Logger(__name__)  # 로깅을 위한 유틸리티
        self.validator = Validator()    # 데이터 검증을 위한 유틸리티
        
        # 작업 상태 초기화
        self.current_task = None
        self.task_context = {}
        self.task_history = []
        self.last_updated = None
        
        # 작업 상태 상수
        self.STATUS_PENDING = 'pending'
        self.STATUS_IN_PROGRESS = 'in_progress'
        self.STATUS_COMPLETED = 'completed'
        self.STATUS_FAILED = 'failed'

    def set_current_task(self, task: Dict) -> bool:
        """
        현재 작업 설정
        
        Args:
            task (Dict): 작업 정보
            
        Returns:
            bool: 설정 성공 여부
        """
        try:
            if not self.validator.validate_task(task):
                raise ValueError("유효하지 않은 작업 형식")
                
            self.current_task = task
            self.task_context = {
                'start_time': datetime.now().isoformat(),
                'status': self.STATUS_IN_PROGRESS,
                'progress': 0,
                'last_activity': datetime.now().isoformat()
            }
            
            self.last_updated = datetime.now()
            self.logger.log_info(f"현재 작업 설정 완료: {task.get('id', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"현재 작업 설정 중 오류 발생: {str(e)}")
            return False

    def get_current_task(self) -> Optional[Dict]:
        """
        현재 작업 정보 조회
        
        Returns:
            Optional[Dict]: 현재 작업 정보
        """
        return self.current_task

    def get_task_context(self) -> Dict:
        """
        현재 작업 컨텍스트 조회
        
        Returns:
            Dict: 작업 컨텍스트 정보
        """
        return self.task_context

    def update_progress(self, progress: float) -> bool:
        """
        작업 진행률 업데이트
        
        Args:
            progress (float): 진행률 (0.0 ~ 1.0)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            if not 0 <= progress <= 1:
                raise ValueError("진행률은 0에서 1 사이여야 합니다")
                
            if not self.current_task:
                raise ValueError("현재 작업이 설정되지 않았습니다")
                
            self.task_context['progress'] = progress
            self.task_context['last_activity'] = datetime.now().isoformat()
            self.last_updated = datetime.now()
            
            if progress >= 1.0:
                self.complete_task()
                
            return True
            
        except Exception as e:
            self.logger.log_error(f"진행률 업데이트 중 오류 발생: {str(e)}")
            return False

    def complete_task(self) -> bool:
        """
        현재 작업 완료 처리
        
        Returns:
            bool: 완료 처리 성공 여부
        """
        try:
            if not self.current_task:
                raise ValueError("현재 작업이 설정되지 않았습니다")
                
            # 작업 완료 처리
            self.task_context['status'] = self.STATUS_COMPLETED
            self.task_context['end_time'] = datetime.now().isoformat()
            self.task_context['progress'] = 1.0
            
            # 작업 이력에 추가
            self.task_history.append({
                'task': self.current_task,
                'context': self.task_context.copy()
            })
            
            # 현재 작업 초기화
            self.current_task = None
            self.task_context = {}
            self.last_updated = datetime.now()
            
            self.logger.log_info("작업 완료 처리 완료")
            return True
            
        except Exception as e:
            self.logger.log_error(f"작업 완료 처리 중 오류 발생: {str(e)}")
            return False

    def fail_task(self, error_message: str) -> bool:
        """
        현재 작업 실패 처리
        
        Args:
            error_message (str): 오류 메시지
            
        Returns:
            bool: 실패 처리 성공 여부
        """
        try:
            if not self.current_task:
                raise ValueError("현재 작업이 설정되지 않았습니다")
                
            # 작업 실패 처리
            self.task_context['status'] = self.STATUS_FAILED
            self.task_context['end_time'] = datetime.now().isoformat()
            self.task_context['error'] = error_message
            
            # 작업 이력에 추가
            self.task_history.append({
                'task': self.current_task,
                'context': self.task_context.copy()
            })
            
            # 현재 작업 초기화
            self.current_task = None
            self.task_context = {}
            self.last_updated = datetime.now()
            
            self.logger.log_info(f"작업 실패 처리 완료: {error_message}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"작업 실패 처리 중 오류 발생: {str(e)}")
            return False

    def get_task_history(self) -> list:
        """
        작업 이력 조회
        
        Returns:
            list: 작업 이력 목록
        """
        return self.task_history

    def clear_history(self) -> bool:
        """
        작업 이력 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self.task_history = []
            self.last_updated = datetime.now()
            self.logger.log_info("작업 이력 초기화 완료")
            return True
        except Exception as e:
            self.logger.log_error(f"작업 이력 초기화 중 오류 발생: {str(e)}")
            return False 