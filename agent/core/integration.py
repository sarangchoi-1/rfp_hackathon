# agent/core/integration.py
from typing import Dict
import logging
# from .category_chain import create_category_chain
# from .task_chain2 import create_task_chain
# from .outline_chain import create_outline_chain
# from .result_composer import ResultComposer
import importlib.util
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

task_chain2_path = os.path.join(project_root, 'core', 'task_chain2.py')
spec = importlib.util.spec_from_file_location("task_chain2", task_chain2_path)
task_chain2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task_chain2)

outline_chain_path = os.path.join(project_root, 'core', 'outline_chain.py')
spec = importlib.util.spec_from_file_location("outline_chain", outline_chain_path)
outline_chain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outline_chain)

result_composer_path = os.path.join(project_root, 'core', 'result_composer.py')
spec = importlib.util.spec_from_file_location("result_composer", result_composer_path)
result_composer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(result_composer)

category_matcher_path = os.path.join(project_root, 'core', 'category_matcher.py')
spec = importlib.util.spec_from_file_location("category_matcher", category_matcher_path)
category_matcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(category_matcher)
logger = logging.getLogger(__name__)

class AgentIntegration:
    """
    에이전트 통합 클래스
    RFP 생성을 위한 여러 컴포넌트를 통합하고 조정합니다.
    """
    
    def __init__(self):
        self.category_matcher = category_matcher.CategoryMatcher()
        self.task_chain = task_chain2.create_task_chain()
        self.outline_chain = outline_chain.create_outline_chain()
        self.result_composer = result_composer.ResultComposer()
        
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
            categories = self.category_matcher.match_task_to_categories({"description": description})
            
            # 작업 분해 및 개요 생성
            task_result = self.task_chain.invoke({
                "request": project_info.get("additional_context", [""])[0],
                "context": description,
                "purpose_analysis": "프로젝트의 목적과 목표를 분석합니다.",
                "scope_definition": "프로젝트의 범위와 요구사항을 정의합니다.",
                "case_study": "유사 사례와 교훈을 분석합니다.",
                "evaluation_criteria": "성공 지표와 품질 기준을 정의합니다."
            })
            outline_result = self.outline_chain.invoke(task_result,[category['category_id'] for category in categories][:3])
            
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
            
agentIntegration = AgentIntegration()
print(agentIntegration.process_request({
            "project_name": None,
            "goal": None,
            "requirements": [],
            "constraints": [],
            "timeline": None,
            "budget": None,
            "stakeholders": [],
            "additional_context": ["대출 부도 예측 모델 고도화 시스템을 구축할래"]
        }))