"""
RFP 응답서 개요 생성 모듈 (Outline Generator Module)
카테고리화된 작업을 기반으로 RFP 응답서의 구조화된 개요를 생성합니다.

이 모듈은 다음과 같은 작업을 수행합니다:
1. 입력된 텍스트를 여러 카테고리로 분류
2. RAG를 사용하여 관련 예시와 템플릿 검색
3. 도메인별(의료/금융) 표준 구조 적용
4. ResultComposer와의 통합을 위한 메타데이터 생성
"""

from typing import List, Dict, Optional
from utils.logger import Logger
from utils.validators import Validator
from utils.exceptions import OutlineError
from ..memory.short_term import ShortTermMemory
from ..memory.long_term import LongTermMemory
from config.settings import Settings
import numpy as np

# RAG(Retrieval-Augmented Generation) 파이프라인 임포트 시도
# RAG는 벡터 데이터베이스를 사용하여 관련 문서를 검색하고 생성에 활용합니다
try:
    from rag_pipeline.vector_store import VectorStore
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    Logger(__name__).log_warning("RAG 파이프라인이 설치되지 않았습니다. 예시 검색 기능이 제한됩니다.")

class OutlineGenerator:
    """
    RFP 응답서 개요 생성기 클래스
    카테고리화된 작업을 기반으로 구조화된 개요를 생성합니다.
    """
    
    def __init__(self):
        # 기본 유틸리티 초기화
        self.logger = Logger(__name__)  # 로깅을 위한 유틸리티
        self.validator = Validator()    # 데이터 검증을 위한 유틸리티
        self.settings = Settings()      # 설정 관리를 위한 유틸리티
        
        # 메모리 시스템 초기화
        self.short_term_memory = ShortTermMemory()  # 최근 작업 내용 저장
        self.long_term_memory = LongTermMemory()    # 과거 작업 결과 저장
        
        # RAG 파이프라인 초기화
        self.vector_store = None
        if RAG_AVAILABLE:
            try:
                self.vector_store = VectorStore()  # 벡터 저장소 초기화
                self.logger.log_info("RAG 파이프라인이 성공적으로 초기화되었습니다.")
            except Exception as e:
                self.logger.log_warning(f"RAG 파이프라인 초기화 실패: {str(e)}")
                RAG_AVAILABLE = False
        
        # 도메인별 기본 구조 정의
        # 의료와 금융 도메인에 대한 표준 섹션 구조를 정의합니다
        self.domain_structures = {
            'medical': {
                'sections': [
                    {'id': 'executive_summary', 'title': '요약', 'weight': 1.0},
                    {'id': 'project_overview', 'title': '프로젝트 개요', 'weight': 1.2},
                    {'id': 'technical_solution', 'title': '기술 솔루션', 'weight': 1.5},
                    {'id': 'implementation_plan', 'title': '구현 계획', 'weight': 1.3},
                    {'id': 'quality_assurance', 'title': '품질 보증', 'weight': 1.1},
                    {'id': 'compliance', 'title': '규정 준수 및 보안', 'weight': 1.4},
                    {'id': 'team_organization', 'title': '팀 구성', 'weight': 1.0},
                    {'id': 'cost_proposal', 'title': '비용 제안', 'weight': 1.0}
                ],
                'keywords': ['의료', '환자', '진료', '병원', '처방', '약품', '검진']
            },
            'finance': {
                'sections': [
                    {'id': 'executive_summary', 'title': '요약', 'weight': 1.0},
                    {'id': 'project_overview', 'title': '프로젝트 개요', 'weight': 1.2},
                    {'id': 'technical_solution', 'title': '기술 솔루션', 'weight': 1.5},
                    {'id': 'implementation_plan', 'title': '구현 계획', 'weight': 1.3},
                    {'id': 'risk_management', 'title': '리스크 관리', 'weight': 1.4},
                    {'id': 'compliance', 'title': '규정 준수 및 보안', 'weight': 1.4},
                    {'id': 'team_organization', 'title': '팀 구성', 'weight': 1.0},
                    {'id': 'cost_proposal', 'title': '비용 제안', 'weight': 1.0}
                ],
                'keywords': ['금융', '투자', '보험', '은행', '증권', '대출', '예금']
            }
        }
        
        # 섹션별 하위 항목 템플릿
        # 각 섹션에 포함될 세부 항목들을 정의합니다
        self.section_templates = {
            'executive_summary': [
                '프로젝트 목표',
                '주요 이점',
                '제안 솔루션 개요'
            ],
            'project_overview': [
                '배경',
                '범위',
                '목표',
                '산출물'
            ],
            'technical_solution': [
                '시스템 아키텍처',
                '주요 기능',
                '연동 포인트',
                '기술 요구사항'
            ],
            'implementation_plan': [
                '단계',
                '일정',
                '마일스톤',
                '리소스 할당'
            ],
            'quality_assurance': [
                '테스트 전략',
                '품질 지표',
                '검증 방법'
            ],
            'compliance': [
                '보안 조치',
                '데이터 보호',
                '규정 준수'
            ],
            'risk_management': [
                '리스크 평가',
                '대응 전략',
                '비상 계획'
            ],
            'team_organization': [
                '프로젝트 구조',
                '주요 인력',
                '역할 및 책임'
            ],
            'cost_proposal': [
                '비용 내역',
                '지불 일정',
                '조건 및 약관'
            ]
        }

        # ResultComposer와의 통합을 위한 메타데이터 구조
        # 문서의 버전, 언어, 생성자 등의 정보를 포함합니다
        self.metadata_template = {
            'version': '1.0',
            'language': 'ko',
            'generated_by': 'OutlineGenerator',
            'last_modified': None,
            'sections': {
                'medical': {
                    'ko': {
                        'executive_summary': '요약',
                        'project_overview': '프로젝트 개요',
                        'technical_solution': '기술 솔루션',
                        'implementation_plan': '구현 계획',
                        'quality_assurance': '품질 보증',
                        'compliance': '규정 준수 및 보안',
                        'team_organization': '팀 구성',
                        'cost_proposal': '비용 제안'
                    }
                },
                'finance': {
                    'ko': {
                        'executive_summary': '요약',
                        'project_overview': '프로젝트 개요',
                        'technical_solution': '기술 솔루션',
                        'implementation_plan': '구현 계획',
                        'risk_management': '리스크 관리',
                        'compliance': '규정 준수 및 보안',
                        'team_organization': '팀 구성',
                        'cost_proposal': '비용 제안'
                    }
                }
            }
        }

    def _get_domain_specific_sections(self, category: str) -> List[Dict]:
        """
        도메인별 섹션 구조 반환
        의료 또는 금융 도메인에 맞는 섹션 구조를 반환합니다.
        """
        return self.domain_structures.get(category, {}).get('sections', [])

    def _get_section_template(self, section_id: str) -> List[str]:
        """
        섹션별 하위 항목 템플릿 반환
        각 섹션에 포함될 세부 항목 목록을 반환합니다.
        """
        return self.section_templates.get(section_id, [])

    def _calculate_section_relevance(self, section: Dict, tasks: List[Dict]) -> float:
        """
        섹션과 작업 간의 관련성 점수 계산
        키워드 매칭과 카테고리 매칭을 통해 관련성을 계산합니다.
        """
        relevance_scores = []
        
        for task in tasks:
            # 섹션 ID와 작업 카테고리 매칭
            if section['id'] in task.get('categories', []):
                relevance_scores.append(1.0)
            else:
                # 키워드 기반 관련성 계산
                section_keywords = set(section['title'].lower().split())
                task_keywords = set(task['description'].lower().split())
                overlap = len(section_keywords.intersection(task_keywords))
                relevance = overlap / max(len(section_keywords), len(task_keywords))
                relevance_scores.append(relevance)
        
        return np.mean(relevance_scores) if relevance_scores else 0.0

    def _get_rag_examples(self, section_id: str, category: str) -> List[Dict]:
        """
        RAG를 사용하여 관련 예시 검색
        벡터 저장소에서 관련 예시와 템플릿을 검색합니다.
        """
        if not RAG_AVAILABLE or not self.vector_store:
            return []
            
        try:
            # 섹션별 검색 쿼리 구성
            query = f"{section_id} {category} example template"
            examples = self.vector_store.search(query, top_k=3)
            return examples
        except Exception as e:
            self.logger.log_warning(f"RAG 예시 검색 중 오류 발생: {str(e)}")
            return []

    def _get_localized_title(self, section_id: str, category: str, language: str = 'ko') -> str:
        """
        지역화된 섹션 제목 반환
        카테고리와 섹션 ID에 해당하는 한국어 제목을 반환합니다.
        """
        try:
            return self.metadata_template['sections'][category]['ko'][section_id]
        except KeyError:
            return section_id.replace('_', ' ').title()

    def _generate_section_outline(self, section: Dict, tasks: List[Dict], category: str) -> Dict:
        """
        섹션별 개요 생성
        각 섹션의 구조, 관련 작업, 예시 등을 포함한 개요를 생성합니다.
        """
        # 기본 템플릿 가져오기
        subsections = self._get_section_template(section['id'])
        
        # 관련 작업 필터링
        relevant_tasks = [t for t in tasks if section['id'] in t.get('categories', [])]
        
        # RAG 예시 검색
        rag_examples = self._get_rag_examples(section['id'], category)
        
        # 섹션 관련성 계산
        relevance = self._calculate_section_relevance(section, tasks)
        
        # 한국어 제목 추가
        title = self._get_localized_title(section['id'], category)
        
        return {
            'id': section['id'],
            'title': title,
            'relevance': relevance,
            'subsections': subsections,
            'relevant_tasks': relevant_tasks,
            'examples': rag_examples,
            'language': 'ko',
            'metadata': {
                'category': category,
                'section_type': section['id'],
                'generated_at': None,
                'last_modified': None
            }
        }

    def generate_outline(self, tasks: List[Dict], primary_category: str) -> Dict:
        """
        RFP 응답서 개요 생성
        작업 목록과 주요 카테고리를 기반으로 전체 개요를 생성합니다.
        
        Args:
            tasks (List[Dict]): 카테고리화된 작업 목록
            primary_category (str): 주요 카테고리 ('medical' 또는 'finance')
            
        Returns:
            Dict: 구조화된 개요
        """
        try:
            # 입력 검증
            if not self.validator.validate_tasks(tasks):
                raise OutlineError("유효하지 않은 작업 형식")
                
            if primary_category not in self.domain_structures:
                raise OutlineError(f"지원하지 않는 카테고리: {primary_category}")
            
            # 도메인별 섹션 구조 가져오기
            sections = self._get_domain_specific_sections(primary_category)
            
            # 섹션별 개요 생성
            outline = {
                'category': primary_category,
                'language': 'ko',
                'sections': [],
                'metadata': self.metadata_template.copy()
            }
            
            # 각 섹션에 대한 개요 생성
            for section in sections:
                section_outline = self._generate_section_outline(section, tasks, primary_category)
                outline['sections'].append(section_outline)
            
            # 관련성 점수로 섹션 정렬
            outline['sections'].sort(key=lambda x: x['relevance'], reverse=True)
            
            # ResultComposer 통합을 위한 메타데이터 추가
            outline['metadata'].update({
                'primary_category': primary_category,
                'section_count': len(outline['sections']),
                'generated_at': None,  # ResultComposer에서 설정
                'last_modified': None,  # ResultComposer에서 설정
                'status': 'draft'  # ResultComposer에서 관리
            })
            
            self.logger.log_info(f"개요 생성 완료: {len(outline['sections'])}개 섹션")
            return outline
            
        except Exception as e:
            self.logger.log_error(f"개요 생성 중 오류 발생: {str(e)}")
            raise 