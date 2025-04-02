"""
결과 작성 모듈 (Result Composer Module)
작업 결과를 기반으로 최종 RFP 응답서를 작성합니다.

이 모듈은 다음과 같은 작업을 수행합니다:
1. 작업 결과의 유효성 검증
2. 개요 구조에 따른 섹션 구성
3. 메타데이터 생성 및 관리
4. 최종 문서 구조화
"""

from typing import List, Dict
from utils.logger import Logger
from utils.validators import Validator
from utils.exceptions import CompositionError
from datetime import datetime
from ..memory.memory_system import MemorySystem

class ResultComposer:
    """
    RFP 응답서 결과 작성기 클래스
    작업 결과를 기반으로 최종 RFP 응답서를 작성합니다.
    """
    
    def __init__(self):
        # 기본 유틸리티 초기화
        self.logger = Logger(__name__)  # 로깅을 위한 유틸리티
        self.validator = Validator()    # 데이터 검증을 위한 유틸리티
        
        # 메모리 시스템 초기화
        self.short_term_memory = MemorySystem()  # 최근 작업 내용 저장
        self.working_memory = MemorySystem()      # 현재 작업 상태 저장
        
        # 기본 메타데이터 템플릿
        # 문서의 버전, 언어, 생성자 등의 기본 정보를 포함합니다
        self.metadata_template = {
            'version': '1.0',
            'language': 'ko',
            'generated_by': 'ResultComposer',
            'created_at': None,
            'last_modified': None,
            'status': 'draft',
            'section_count': 0,
            'word_count': 0
        }

    def compose_results(self, task_results: List[Dict], outline: Dict) -> Dict:
        """
        작업 결과를 기반으로 최종 RFP 응답서 작성
        
        Args:
            task_results (List[Dict]): 작업 결과 목록
            outline (Dict): OutlineGenerator에서 생성한 개요
            
        Returns:
            Dict: 최종 RFP 응답서
        """
        try:
            # 입력 검증
            if not self.validate_task_results(task_results):
                raise CompositionError("유효하지 않은 작업 결과 형식")
                
            if not self.validate_outline(outline):
                raise CompositionError("유효하지 않은 개요 형식")

            # 컨텍스트 가져오기
            context = self.short_term_memory.get_recent_context()  # 최근 작업 컨텍스트
            working_state = self.working_memory.get_current_task()  # 현재 작업 상태
            
            # 현재 시간 설정
            current_time = datetime.now().isoformat()
            
            # 기본 구조 초기화
            result = {
                'title': self.generate_title(task_results, outline, context),
                'sections': [],
                'metadata': self.metadata_template.copy(),
                'status': 'draft'
            }
            
            # 섹션 구성
            result['sections'] = self.organize_sections(task_results, outline)
            
            # 메타데이터 업데이트
            result['metadata'].update({
                'created_at': current_time,
                'last_modified': current_time,
                'section_count': len(result['sections']),
                'word_count': self.calculate_word_count(result),
                'primary_category': outline.get('category'),
                'language': outline.get('language', 'ko')
            })
            
            # 최종 검증
            if not self.validate_final_result(result):
                raise CompositionError("유효하지 않은 최종 결과 형식")
            
            self.logger.log_info("RFP 응답서 작성 완료")
            return result

        except Exception as e:
            self.logger.log_error(f"결과 작성 중 오류 발생: {str(e)}")
            raise

    def validate_task_results(self, task_results: List[Dict]) -> bool:
        """
        작업 결과 구조 검증
        작업 결과의 형식과 내용이 올바른지 검증합니다.
        """
        try:
            if not isinstance(task_results, list):
                return False
                
            for result in task_results:
                if not self.validator.validate_task_result(result):
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.log_error(f"작업 결과 검증 중 오류 발생: {str(e)}")
            return False

    def generate_title(self, task_results: List[Dict], outline: Dict, context: Dict) -> str:
        """
        RFP 제목 생성
        작업 결과와 개요를 기반으로 적절한 제목을 생성합니다.
        """
        try:
            category = outline.get('category', '')
            primary_task = task_results[0] if task_results else {}
            
            # 기본 제목 템플릿
            templates = {
                'medical': '의료 정보 시스템 {} 제안서',
                'finance': '금융 시스템 {} 제안서'
            }
            
            # 프로젝트 유형 추출
            project_type = primary_task.get('task_type', '')
            
            return templates.get(category, '제안서').format(project_type)
            
        except Exception as e:
            self.logger.log_error(f"제목 생성 중 오류 발생: {str(e)}")
            return '제안서'

    def organize_sections(self, task_results: List[Dict], outline: Dict) -> List[Dict]:
        """
        작업 결과를 섹션별로 구성
        개요의 섹션 구조에 따라 작업 결과를 정리합니다.
        """
        try:
            sections = []
            
            # 개요의 섹션 구조를 기반으로 구성
            for section in outline.get('sections', []):
                section_id = section['id']
                section_title = section['title']
                
                # 관련 작업 결과 필터링
                relevant_results = [
                    result for result in task_results 
                    if section_id in result.get('categories', [])
                ]
                
                # 섹션 구성
                section_content = {
                    'id': section_id,
                    'title': section_title,
                    'content': relevant_results,
                    'subsections': section.get('subsections', []),
                    'examples': section.get('examples', []),
                    'metadata': {
                        'task_count': len(relevant_results),
                        'generated_at': datetime.now().isoformat(),
                        'last_modified': datetime.now().isoformat()
                    }
                }
                
                sections.append(section_content)
            
            return sections
            
        except Exception as e:
            self.logger.log_error(f"섹션 구성 중 오류 발생: {str(e)}")
            return []

    def calculate_word_count(self, result: Dict) -> int:
        """
        전체 문서의 단어 수 계산
        제목과 섹션 내용의 단어 수를 합산합니다.
        """
        try:
            total_words = 0
            
            # 제목 단어 수
            for title in result['title'].values():
                total_words += len(title.split())
            
            # 섹션 내용 단어 수
            for section in result['sections']:
                for content in section['content']:
                    if isinstance(content, dict) and 'description' in content:
                        total_words += len(content['description'].split())
            
            return total_words
            
        except Exception as e:
            self.logger.log_error(f"단어 수 계산 중 오류 발생: {str(e)}")
            return 0

    def validate_outline(self, outline: Dict) -> bool:
        """
        개요 구조 검증
        개요의 필수 필드가 모두 포함되어 있는지 검증합니다.
        """
        try:
            required_fields = ['category', 'sections', 'metadata']
            return all(field in outline for field in required_fields)
        except Exception:
            return False

    def validate_final_result(self, result: Dict) -> bool:
        """
        최종 결과 구조 검증
        최종 결과의 필수 필드가 모두 포함되어 있는지 검증합니다.
        """
        try:
            required_fields = ['title', 'sections', 'metadata', 'status']
            return all(field in result for field in required_fields)
        except Exception:
            return False 