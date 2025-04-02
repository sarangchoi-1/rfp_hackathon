# agent/core/integration.py
from typing import Dict
import logging
from .category_chain import create_category_chain
from .task_chain2 import create_task_chain
from .outline_chain import create_outline_chain
from .result_composer import ResultComposer

logger = logging.getLogger(__name__)

class AgentIntegration:
    """
    에이전트 통합 클래스
    RFP 생성을 위한 여러 컴포넌트를 통합하고 조정합니다.
    """
    
    def __init__(self):
        self.category_chain = create_category_chain()
        self.task_chain = create_task_chain()
        self.outline_chain = create_outline_chain()
        self.result_composer = ResultComposer()
        
    def process_request(self, project_info: Dict) -> Dict:
        """
        프로젝트 정보를 처리하여 RFP 개요를 생성합니다.
        
        Args:
            project_info (Dict): 프로젝트 이름과 목표를 포함한 정보
            
        Returns:
            Dict: 생성된 RFP 개요와 관련 정보
        """
        try:
            # 프로젝트 설명 준비
            description = f"{project_info.get('project_name', '')} - {project_info.get('goal', '')}"
            
            # 카테고리 매칭
            categories = self.category_chain.match_task_to_categories({"description": description})
            
            # 작업 분해 및 개요 생성
            task_result = self.task_chain.run(project_info)
            outline_result = self.outline_chain.run(task_result)
            
            # RAG 파이프라인 응답 (실제 구현 시 RAG 파이프라인과 연동)
            rag_response = "RAG 파이프라인 응답이 여기에 들어갈 예정입니다."
            
            # 최종 결과 작성
            final_result = self.result_composer.compose(
                outline_result=outline_result,
                rag_response=rag_response,
                project_info=project_info
            )
            
            return {
                "status": "success",
                "categories": categories,
                "outline": final_result,
                "metadata": {
                    "category_count": len(categories),
                    "has_rag_response": bool(rag_response)
                }
            }
            
        except Exception as e:
            logger.error(f"요청 처리 중 오류 발생: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "categories": [],
                "outline": None,
                "metadata": {}
            }