"""
작업 분해 모듈 (Task Decomposition Module)
사용자의 요청을 구조화된 작업으로 분해하는 핵심 모듈입니다.
RFP(제안요청서) 분석을 위한 작업을 체계적으로 분류하고 우선순위를 부여합니다.

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
    """
    작업 분해기 클래스
    사용자의 요청을 분석하여 체계적인 작업 단위로 분해합니다.
    각 작업은 고유 ID, 유형, 설명, 우선순위, 의존성을 가집니다.
    """
    
    def __init__(self):
        # 기본 유틸리티 초기화
        self.logger = Logger(__name__)  # 로깅 시스템
        self.validator = Validator()    # 데이터 검증기
        
        # 메모리 시스템 초기화
        self.short_term_memory = ShortTermMemory()  # 단기 기억 (최근 컨텍스트)
        self.long_term_memory = LongTermMemory()    # 장기 기억 (과거 데이터)
        self.working_memory = WorkingMemory()       # 작업 기억 (현재 처리 중인 데이터)
        
        # 작업 유형 정의 및 설정
        # priority: 우선순위 (낮을수록 중요)
        # keywords: 작업 식별을 위한 키워드
        # dependencies: 의존성 있는 다른 작업 유형
        self.task_types = {
            'purpose': {
                'priority': 1,
                'keywords': [
                    '목적', '목표', '배경', '필요성', 'why', 'purpose', 'objective',
                    '기대효과', '기대', '성과', '효과', 'outcome', 'impact', 'benefit',
                    '문제', '현황', '상황', 'problem', 'status', 'situation'
                ],
                'dependencies': []
            },
            'scope': {
                'priority': 2,
                'keywords': [
                    '범위', '규모', '기간', '대상', 'scope', 'scale', 'timeline',
                    '예산', '비용', '금액', '재정', 'budget', 'cost', 'financial',
                    '인력', '자원', '리소스', 'resource', 'manpower', 'staff'
                ],
                'dependencies': ['purpose']
            },
            'case': {
                'priority': 3,
                'keywords': [
                    '사례', '예시', '참고', '벤치마크', 'case', 'example', 'reference',
                    '표준', '기준', '업계', '시장', 'standard', 'industry', 'market',
                    '방법론', '기술', '접근', 'methodology', 'technology', 'approach'
                ],
                'dependencies': ['scope']
            },
            'evaluation': {
                'priority': 4,
                'keywords': [
                    '평가', '기준', '지표', '점수', 'evaluation', 'criteria', 'metrics',
                    '정성', '질적', '주관', 'qualitative', 'subjective', 'quality',
                    '산출물', '결과물', '성과물', 'deliverable', 'output', 'result'
                ],
                'dependencies': ['scope', 'case']
            }
        }

    def decompose_request(self, user_request: str) -> List[Dict]:
        """
        사용자 요청을 구조화된 작업으로 분해하는 메인 메서드
        
        Args:
            user_request (str): 사용자의 원본 요청 텍스트
            
        Returns:
            List[Dict]: 작업 목록. 각 작업은 다음 정보를 포함:
                - task_id: 작업 고유 식별자
                - task_type: 작업 유형 (purpose/scope/case/evaluation)
                - description: 작업 설명
                - priority: 우선순위
                - dependencies: 의존성 있는 작업 ID 목록
                
        Raises:
            TaskError: 작업 구조가 유효하지 않은 경우
        """
        try:
            # 최근 컨텍스트 가져오기
            context = self.short_term_memory.get_recent_context()
            
            # 작업 목록 초기화
            tasks = []
            
            # 각 작업 유형별로 작업 생성
            for task_type, config in self.task_types.items():
                task_id = str(uuid.uuid4())[:8]  # 고유 ID 생성
                description = self._generate_task_description(user_request, task_type, config['keywords'])
                
                task = {
                    'task_id': task_id,
                    'task_type': task_type,
                    'description': description,
                    'priority': config['priority'],
                    'dependencies': self._get_dependencies(task_id, task_type, tasks)
                }
                tasks.append(task)
            
            # 컨텍스트 기반 우선순위 조정
            tasks = self._adjust_priorities(tasks, context)
            
            # 작업 유효성 검증
            if not self.validate_tasks(tasks):
                raise TaskError("유효하지 않은 작업 구조")
            
            # 작업 메모리에 저장
            self.working_memory.set_current_task({'tasks': tasks, 'request': user_request})
            
            self.logger.log_info(f"요청을 {len(tasks)}개의 작업으로 성공적으로 분해")
            return tasks
            
        except Exception as e:
            self.logger.log_error(f"요청 분해 중 오류 발생: {str(e)}")
            raise

    def _generate_task_description(self, request: str, task_type: str, keywords: List[str]) -> str:
        """
        작업 설명 생성 메서드
        
        Args:
            request (str): 사용자 요청 텍스트
            task_type (str): 작업 유형
            keywords (List[str]): 작업 식별 키워드
            
        Returns:
            str: 생성된 작업 설명
        """
        try:
            # 작업 유형별 기본 프롬프트 정의
            prompts = {
                'purpose': "RFP의 목적과 배경을 파악하여 정리: 1) 프로젝트의 추진 배경, 2) 핵심 목표와 기대효과, 3) 현재 상황 및 문제점, 4) 성공 기준",
                'scope': "프로젝트의 범위와 규모를 정의: 1) 수행 범위와 제외 범위, 2) 예산 규모, 3) 수행 기간 및 주요 마일스톤, 4) 투입 인력 요구사항",
                'case': "관련 사례와 참고 자료 조사: 1) 유사 프로젝트 성공 사례, 2) 업계 표준 및 벤치마크, 3) 적용 가능한 기술/방법론, 4) 리스크 및 대응 방안",
                'evaluation': "평가 기준과 지표 설정: 1) 정량적 평가 지표, 2) 정성적 평가 기준, 3) 단계별 산출물 요구사항, 4) 검수 및 승인 절차"
            }
            
            # 키워드 기반 관련 내용 추출
            relevant_parts = []
            for keyword in keywords:
                pattern = f"[^.]*{keyword}[^.]*\\."
                matches = re.findall(pattern, request, re.IGNORECASE)
                relevant_parts.extend(matches)
            
            # 기본 프롬프트와 관련 내용 결합
            description = f"{prompts[task_type]}"
            if relevant_parts:
                description += f" (관련 내용: {' '.join(relevant_parts)})"
            
            return description.strip()
            
        except Exception as e:
            self.logger.log_error(f"작업 설명 생성 중 오류 발생: {str(e)}")
            return prompts[task_type]  # 기본 프롬프트로 폴백

    def _get_dependencies(self, task_id: str, task_type: str, existing_tasks: List[Dict]) -> List[str]:
        """
        작업 의존성 관리 메서드
        
        Args:
            task_id (str): 현재 작업 ID
            task_type (str): 작업 유형
            existing_tasks (List[Dict]): 기존 작업 목록
            
        Returns:
            List[str]: 의존성 있는 작업 ID 목록
        """
        try:
            dependencies = []
            required_types = self.task_types[task_type]['dependencies']
            
            for task in existing_tasks:
                if task['task_type'] in required_types:
                    dependencies.append(task['task_id'])
            
            return dependencies
            
        except Exception as e:
            self.logger.log_error(f"의존성 확인 중 오류 발생: {str(e)}")
            return []

    def _adjust_priorities(self, tasks: List[Dict], context: Dict) -> List[Dict]:
        """
        작업 우선순위 조정 메서드
        
        Args:
            tasks (List[Dict]): 작업 목록
            context (Dict): 현재 컨텍스트
            
        Returns:
            List[Dict]: 우선순위가 조정된 작업 목록
        """
        try:
            # 과거 성과 데이터 가져오기
            history = self.long_term_memory.get_task_history()
            
            for task in tasks:
                base_priority = task['priority']
                
                # 과거 성공률 기반 우선순위 조정
                if history and task['task_type'] in history:
                    success_rate = history[task['task_type']].get('success_rate', 1.0)
                    task['priority'] = int(base_priority / success_rate)
                
                # 의존성 수에 따른 우선순위 조정
                if task['dependencies']:
                    task['priority'] += len(task['dependencies'])
            
            # 우선순위 기준 정렬
            tasks.sort(key=lambda x: x['priority'])
            return tasks
            
        except Exception as e:
            self.logger.log_error(f"우선순위 조정 중 오류 발생: {str(e)}")
            return tasks

    def validate_tasks(self, tasks: List[Dict]) -> bool:
        """
        작업 유효성 검증 메서드
        
        Args:
            tasks (List[Dict]): 검증할 작업 목록
            
        Returns:
            bool: 모든 작업이 유효한 경우 True
        """
        try:
            if not isinstance(tasks, list):
                return False
            
            task_ids = set()
            for task in tasks:
                if not self.validator.validate_task(task):
                    return False
                    
                # 중복 작업 ID 확인
                if task['task_id'] in task_ids:
                    return False
                task_ids.add(task['task_id'])
                
                # 작업 유형 유효성 확인
                if task['task_type'] not in self.task_types:
                    return False
                
                # 의존성 유효성 확인
                for dep_id in task['dependencies']:
                    if dep_id not in task_ids:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"작업 검증 중 오류 발생: {str(e)}")
            return False 