"""
결과 작성 모듈 (Result Composer Module)
작업 결과를 기반으로 최종 RFP 응답서를 작성합니다.
"""

from typing import List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ResultComposer:
    """
    RFP 응답서 결과 작성기 클래스
    작업 결과를 기반으로 최종 RFP 응답서를 작성합니다.
    """
    
    def __init__(self):
        # 기본 메타데이터 템플릿
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

    def compose(self, outline_result: Dict, rag_response: str, project_info: Dict, categories: List[str] = None) -> Dict:
        """
        작업 결과를 기반으로 최종 RFP 응답서를 작성합니다.
        
        Args:
            outline_result (Dict): 개요 생성 결과
            rag_response (str): RAG 파이프라인 응답
            project_info (Dict): 프로젝트 정보
            categories (List[str], optional): 매칭된 카테고리 목록
            
        Returns:
            Dict: 작성된 RFP 응답서
        """
        try:
            # 기본 메타데이터 템플릿
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "categories": categories or [],
                "has_rag_context": bool(rag_response)
            }
            
            # 개요 결과와 메타데이터 결합
            result = {
                **outline_result,
                "metadata": metadata
            }
            
            # RAG 컨텍스트가 있는 경우 추가
            if rag_response:
                result["additional_context"] = rag_response
                
            return result
            
        except Exception as e:
            logger.error(f"결과 작성 중 오류 발생: {str(e)}")
            raise Exception(f"결과 작성 실패: {str(e)}") 