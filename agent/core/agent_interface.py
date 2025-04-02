from typing import Dict, List, Any
import logging
from agent.memory.memory_system import MemorySystem
from agent.memory.memory_state import AgentState
from agent.core.category_chain import create_category_chain
from agent.core.task_chain2 import (
    create_purpose_analysis_chain,
    create_scope_definition_chain,
    create_case_study_chain,
    create_evaluation_criteria_chain,
    create_task_chain
)
from agent.core.outline_chain import create_outline_chain
from agent.core.result_composer import ResultComposer
from agent.core.performance_monitoring import PerformanceMonitor
from agent.core.category_matcher import CategoryMatcher
from rag_pipeline.rag_pipeline import rag_pipeline
from langchain_openai import ChatOpenAI
import json

logger = logging.getLogger(__name__)

class AgentInterface:
    """
    에이전트 인터페이스
    RFP 생성을 위한 모든 컴포넌트를 통합하고 조정합니다.
    """
    
    def __init__(self):
        # Initialize core components
        self.memory = MemorySystem()
        self.category_chain = create_category_chain()
        self.category_matcher = CategoryMatcher()
        self.purpose_chain = create_purpose_analysis_chain()
        self.scope_chain = create_scope_definition_chain()
        self.case_chain = create_case_study_chain()
        self.eval_chain = create_evaluation_criteria_chain()
        self.task_chain = create_task_chain()
        self.outline_chain = create_outline_chain()
        self.result_composer = ResultComposer()
        self.performance_monitor = PerformanceMonitor()
        self.llm = ChatOpenAI()
        
        # Initialize conversation state
        self.conversation_state = {
            "current_topic": None,
            "last_question": None,
            "follow_up_count": 0,
            "extracted_info": {},
            "missing_info": set(["project_name", "goal"] + [
                "requirements", "constraints", "timeline", 
                "budget", "stakeholders"
            ])
        }
        
        # Required fields for minimum viable outline
        self.required_fields = ["project_name", "goal"]
        
        # Optional fields for enhanced outline
        self.optional_fields = [
            "requirements", "constraints", "timeline", 
            "budget", "stakeholders"
        ]

    def analyze_conversation(self, project_info: Dict[str, Any], messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze the conversation history to extract and track information."""
        # Start performance monitoring
        self.performance_monitor.start_operation("conversation_analysis")
        
        try:
            # Convert messages to a format suitable for analysis
            conversation_text = "\n".join([
                f"{'User' if msg['is_user'] else 'Assistant'}: {msg['content']}"
                for msg in messages
            ])
            
            # Analyze the conversation to extract information
            analysis_prompt = f"""
            다음 대화 내용을 분석하여 프로젝트 관련 정보를 추출해주세요:
            
            대화 내용:
            {conversation_text}
            
            현재 프로젝트 정보:
            {project_info}
            """
            
            # Use the purpose chain to analyze the conversation
            analysis_result = self.purpose_chain.invoke({
                "request": analysis_prompt,
                "context": project_info.get("additional_context", [])
            })
            
            # Handle the response based on its type
            if hasattr(analysis_result, 'function_call') and analysis_result.function_call:
                # If it's a function call response, parse the arguments
                result_data = json.loads(analysis_result.function_call.arguments)
            elif hasattr(analysis_result, 'model_dump'):
                # If it's a Pydantic model, convert to dict
                result_data = analysis_result.model_dump()
            else:
                # If it's already a dict, use it as is
                result_data = analysis_result
            
            # Update conversation state using the result data
            self.conversation_state.update({
                "current_topic": result_data.get("next_topic", ""),
                "extracted_info": result_data.get("extracted_info", {}),
                "missing_info": set(result_data.get("missing_info", [])),
                "conversation_context": result_data.get("conversation_context", "")
            })
            
            # Store in memory system using add_interaction
            self.memory.add_interaction({
                "type": "conversation_analysis",
                "state": self.conversation_state,
                "result_data": result_data
            })
            
            return {
                "next_topic": result_data.get("next_topic", ""),
                "conversation_context": result_data.get("conversation_context", ""),
                "extracted_info": result_data.get("extracted_info", {}),
                "missing_info": result_data.get("missing_info", [])
            }
            
        finally:
            # End performance monitoring
            self.performance_monitor.end_operation("conversation_analysis")

    def should_continue_conversation(self, project_info: Dict[str, Any]) -> bool:
        """Determine if more information is needed."""
        # Start performance monitoring
        self.performance_monitor.start_operation("conversation_continuation_check")
        
        try:
            # Calculate completeness score
            required_completeness = sum(
                1 for field in self.required_fields 
                if project_info.get(field) or field in self.conversation_state["extracted_info"]
            ) / len(self.required_fields)
            
            optional_completeness = sum(
                1 for field in self.optional_fields 
                if project_info.get(field) or field in self.conversation_state["extracted_info"]
            ) / len(self.optional_fields)
            
            # Overall completeness score (weighted towards required fields)
            total_completeness = (required_completeness * 0.7) + (optional_completeness * 0.3)
            
            # Continue if required fields are not complete or if we have significant missing optional info
            return required_completeness < 0.8 or (total_completeness < 0.5 and self.conversation_state["follow_up_count"] < 3)
            
        finally:
            # End performance monitoring
            self.performance_monitor.end_operation("conversation_continuation_check")

    def generate_next_question(self, project_info: Dict[str, Any], messages: List[Dict[str, str]]) -> str:
        """Generate the next question based on conversation history and current context."""
        # Start performance monitoring
        self.performance_monitor.start_operation("question_generation")
        
        try:
            # Analyze the conversation
            analysis = self.analyze_conversation(project_info, messages)
            
            # Get the current topic and missing information
            current_topic = self.conversation_state["current_topic"]
            missing_info = self.conversation_state["missing_info"]
            
            # Generate a contextual question
            question_prompt = f"""
            다음 정보를 바탕으로 자연스러운 다음 질문을 생성해주세요:
            
            현재 주제: {current_topic}
            누락된 정보: {missing_info}
            대화 맥락: {self.conversation_state['conversation_context']}
            마지막 질문: {self.conversation_state['last_question']}
            
            다음 규칙을 따라주세요:
            1. 이전 대화 맥락을 고려하여 자연스러운 질문을 생성
            2. 누락된 중요 정보를 우선적으로 요청
            3. 사용자의 이전 답변을 참조하여 구체적인 후속 질문 생성
            4. 대화가 자연스럽게 흐르도록 구성
            """
            
            # Use the purpose chain to generate the question
            question_result = self.purpose_chain.invoke({
                "request": question_prompt,
                "context": project_info.get("additional_context", [])
            })
            
            # Handle the response based on its type
            if hasattr(question_result, 'function_call') and question_result.function_call:
                # If it's a function call response, parse the arguments
                result_data = json.loads(question_result.function_call.arguments)
            elif hasattr(question_result, 'model_dump'):
                # If it's a Pydantic model, convert to dict
                result_data = question_result.model_dump()
            else:
                # If it's already a dict, use it as is
                result_data = question_result
            
            # Update conversation state
            self.conversation_state["last_question"] = result_data.get("question", "")
            self.conversation_state["follow_up_count"] += 1
            
            # Store in memory system using add_interaction
            self.memory.add_interaction({
                "type": "question_generation",
                "state": self.conversation_state,
                "result_data": result_data
            })
            
            return result_data.get("question", "프로젝트에 대해 더 자세히 알려주실 수 있을까요?")
            
        finally:
            # End performance monitoring
            self.performance_monitor.end_operation("question_generation")

    def generate_outline(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트 정보를 기반으로 RFP 개요를 생성합니다.
        
        Args:
            project_info (Dict): 프로젝트 정보
            
        Returns:
            Dict: 생성된 RFP 개요
        """
        # Start performance monitoring
        self.performance_monitor.start_operation("outline_generation")
        
        try:
            # Combine project info with extracted information from conversation
            combined_info = {
                **project_info,
                **self.conversation_state["extracted_info"]
            }
            
            # Prepare project description for RAG
            project_description = f"{combined_info.get('project_name', '')} - {combined_info.get('goal', '')}"
            
            # Get additional context from RAG pipeline
            rag_context = rag_pipeline(project_description)
            
            # Match categories
            categories = self.category_matcher.match_task_to_categories({"description": project_description})
            
            # Combine all context
            full_context = combined_info.get("additional_context", [])
            if rag_context:
                full_context.append(f"관련 사례 및 참고 정보: {rag_context}")
            
            # Generate purpose analysis with RAG context
            purpose_result = self.purpose_chain.invoke({
                "request": combined_info.get("goal", ""),
                "context": full_context
            })
            
            # Generate scope definition with RAG context
            scope_result = self.scope_chain.invoke({
                "request": combined_info.get("goal", ""),
                "context": full_context,
                "purpose_analysis": purpose_result
            })
            
            # Generate case study with RAG context
            case_result = self.case_chain.invoke({
                "request": combined_info.get("goal", ""),
                "context": full_context,
                "purpose_analysis": purpose_result,
                "scope_definition": scope_result
            })
            
            # Generate evaluation criteria with RAG context
            eval_result = self.eval_chain.invoke({
                "request": combined_info.get("goal", ""),
                "context": full_context,
                "purpose_analysis": purpose_result,
                "scope_definition": scope_result,
                "case_study": case_result
            })
            
            # Generate tasks with RAG context
            task_result = self.task_chain.invoke({
                "request": combined_info.get("goal", ""),
                "context": full_context,
                "purpose_analysis": purpose_result,
                "scope_definition": scope_result,
                "case_study": case_result,
                "evaluation_criteria": eval_result
            })
            
            # Generate outline using outline chain
            outline_result = self.outline_chain.invoke(task_result, categories)
            
            # Compose final result
            final_result = self.result_composer.compose(
                outline_result=outline_result,
                rag_response=rag_context,
                project_info=combined_info,
                categories=categories
            )
            
            return {
                "status": "success",
                "outline": final_result,
                "metadata": {
                    "has_rag_context": bool(rag_context),
                    "categories": categories,
                    "performance_metrics": self.performance_monitor.get_metrics()
                }
            }
            
        except Exception as e:
            logger.error(f"개요 생성 중 오류 발생: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "outline": None
            }
            
        finally:
            # End performance monitoring
            self.performance_monitor.end_operation("outline_generation") 