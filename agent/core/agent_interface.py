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
from rag_pipeline.rag_pipeline import double_retrieve, RAGPipeline
from langchain_openai import ChatOpenAI
import json





logger = logging.getLogger(__name__)

class AgentInterface:
    """
    에이전트 인터페이스
    RFP 생성을 위한 모든 컴포넌트를 통합하고 조정합니다.
    """
    
    def __init__(self, memory_system):
        # Initialize core components
        self.memory = memory_system
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
        self.llm = ChatOpenAI(
            temperature=0.3,
            model="gpt-3.5-turbo"  # You can specify the model here
        )
        
        # Initialize conversation state
        self.conversation_state = {
            "requirements": {},
            "identified_topics": set(),
            "confidence_scores": {},
            "missing_information": set(),
            "follow_up_count": 0
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
        # Generate cache key
        cache_key = self.memory.cache.generate_key(
            "conversation_analysis",
            project_info=str(project_info),
            messages=str(messages)
        )
        
        # Try to get from cache
        cached_result = self.memory.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # If not in cache, perform analysis
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
                print("json.loads")
                result_data = json.loads(analysis_result.function_call.arguments)
            elif hasattr(analysis_result, 'model_dump'):
                # If it's a Pydantic model, convert to dict
                print("model_dump")
                result_data = analysis_result.model_dump()
            else:
                # If it's already a dict, use it as is
                print("dict")
                result_data = analysis_result
            result_dic=json.loads(result_data.get("additional_kwargs", {}).get("function_call", {}).get("arguments", {}).replace("\n", ' '))
            # Update conversation state using the result data
            self.conversation_state.update({
                "current_topic": result_dic.get("next_topic", ""),
                "extracted_info": result_data.get("extracted_info", {}),
                "missing_info": result_dic.get("missing_info", []),
                "conversation_context": result_dic.get("conversation_context", ""),
                "question": result_dic.get("question", "")
            })
            
            # Store in memory system using add_interaction
            self.memory.add_interaction({
                "type": "conversation_analysis",
                "state": self.conversation_state,
                "result_data": result_data
            })
            print('\n\n',result_dic,'\n\n')
            result = {
                "next_topic": result_dic.get("next_topic", ""),
                "conversation_context": result_dic.get("conversation_context", ""),
                "extracted_info": result_data.get("extracted_info", {}),
                "missing_info": result_dic.get("missing_info", [])
            }
            
            # Cache the result
            self.memory.cache.set(cache_key, result)
            return result
            
        finally:
            # End performance monitoring
            self.performance_monitor.end_operation("conversation_analysis")

    def should_continue_conversation(self, project_info: Dict[str, Any]) -> bool:
        """Determine if more information is needed."""
        self.performance_monitor.start_operation("conversation_continuation_check")
        
        try:
            # Calculate completeness score
            required_completeness = sum(
                1 for field in self.required_fields 
                if project_info.get(field) or field in self.conversation_state["extracted_info"]
            ) / len(self.required_fields)
            
            # Check if we have enough basic information to start
            if required_completeness >= 0.6:
                # We have enough basic info - generate initial outline
                if not self.conversation_state.get("initial_outline_generated"):
                    self.conversation_state["initial_outline_generated"] = True
                    return False  # Stop asking questions, show initial outline
            
            # If we've asked too many follow-up questions, stop
            if self.conversation_state["follow_up_count"] >= 3:
                return False
            
            # Continue only if we're missing critical information
            return required_completeness < 0.6
            
        finally:
            self.performance_monitor.end_operation("conversation_continuation_check")

    def analyze_user_uncertainty(self, message: str) -> Dict[str, Any]:
        """Quickly analyze if the user is expressing uncertainty and about what topic."""
        uncertainty_prompt = [
            {
                "role": "system",
                "content": """사용자의 메시지에서 불확실성이나 추가 설명이 필요한 부분을 빠르게 분석하세요.
                다음 형식으로 JSON으로 응답하세요:
                {
                    "is_uncertain": boolean,
                    "topic": string or null,
                    "needs_examples": boolean
                }"""
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        try:
            # Use invoke() instead of chat.completions.create
            response = self.llm.invoke(uncertainty_prompt)
            return json.loads(response.content)
        except Exception as e:
            logger.warning(f"Uncertainty analysis failed: {e}")
            return {"is_uncertain": False, "topic": None, "needs_examples": False}

    def generate_next_question(self, project_info: Dict[str, Any], messages: List[Dict[str, str]]) -> str:
        """Generate the next question based on conversation history and current context."""
        self.performance_monitor.start_operation("question_generation")
        
        try:
            # Analyze the conversation
            analysis = self.analyze_conversation(project_info, messages)
            
            # Get the current topic we're focusing on
            current_topic = analysis.get("next_topic") or self.conversation_state.get("current_topic")
            
            # Check user's last message for uncertainty
            last_user_message = next((msg["content"] for msg in reversed(messages) if msg["is_user"]), "")
            uncertainty_analysis = self.analyze_user_uncertainty(last_user_message)
            
            # Always retrieve relevant examples for the current topic
            rag_examples = double_retrieve(current_topic)
            
            if uncertainty_analysis["is_uncertain"]:
                # Generate an explanatory response with examples
                explanation_prompt = f"""
                사용자가 {current_topic}에 대해 불확실해합니다.
                
                대화 맥락: {analysis.get('conversation_context', '')}
                
                관련 사례:
                {rag_examples}
                
                다음 형식으로 응답해주세요:
                1. 간단한 설명 (1-2문장)
                2. 위의 관련 사례를 활용한 구체적인 예시
                3. 하나의 명확한 후속 질문
                """
                
                response_result = self.purpose_chain.invoke({
                    "request": explanation_prompt,
                    "context": project_info.get("additional_context", [])
                })
            else:
                # Focus on a single missing component with examples
                missing_info = analysis.get("missing_info", [])
                if not missing_info:
                    return "지금까지 제공해주신 정보를 바탕으로 RFP를 작성하도록 하겠습니다."
                
                # Select the first missing item to focus on
                focus_topic = missing_info[0]
                
                question_prompt = f"""
                다음 정보를 바탕으로 하나의 구체적인 질문을 생성해주세요:
                
                집중할 주제: {focus_topic}
                현재 맥락: {analysis.get('conversation_context', '')}
                
                관련 사례:
                {rag_examples}
                
                다음 형식으로 응답해주세요:
                1. 관련 사례를 활용한 짧은 예시 설명
                2. 그 맥락에서 이어지는 하나의 구체적인 질문
                
                규칙:
                - 반드시 하나의 질문만 하세요
                - 예시를 먼저 언급한 후 자연스럽게 질문으로 이어가세요
                - 이전 답변을 참조하여 맥락을 유지하세요
                """
                
                response_result = self.purpose_chain.invoke({
                    "request": question_prompt,
                    "context": project_info.get("additional_context", [])
                })
            
            # Extract just the question from the response
            if hasattr(response_result, 'content'):
                content = response_result.content
                # If the content is a structured analysis, extract just the question
                if "누락된 정보에 대한 질문" in content:
                    # Find the questions section and extract the first question
                    questions_section = content.split("누락된 정보에 대한 질문")[1]
                    questions = [q.strip('- ').strip() for q in questions_section.split('\n') if q.strip().startswith('-')]
                    if questions:
                        return questions[0]  # Return just the first question
                
                # If it's a direct question (not in analysis format), return it as is
                if '?' in content:
                    return content

            # Fallback to generate a simple question about missing info
            missing_info = self.conversation_state.get("missing_info", [])
            if missing_info:
                return f"{missing_info[0]}에 대해 좀 더 자세히 알려주실 수 있나요?"
            
            return "프로젝트에 대해 더 자세히 설명해 주시겠어요?"
            
        except Exception as e:
            print(f"Error in generate_next_question: {e}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
        
        finally:
            self.performance_monitor.end_operation("question_generation")

    def generate_outline(self, project_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate RFP outline based on project information."""
        try:
            # Generate the outline
            result = self.purpose_chain.invoke({
                "request": "Generate RFP outline",
                "context": project_info
            })
            
            # Log the result for debugging
            print("Generated outline:", result)
            
            return {
                "outline": result,
                "status": "success"
            }
        except Exception as e:
            print(f"Error generating outline: {e}")
            return {
                "outline": "<p>오류가 발생했습니다.</p>",
                "status": "error"
            }

    def analyze_conversation_realtime(self, message: Dict[str, str], project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze each message in real-time as it arrives."""
        # Try cache first
        cache_key = {
            "message": message,
            "current_state": self.conversation_state,
            "project_info": project_info
        }
        
        cached_analysis = self.memory.cache.get("realtime_analysis", **cache_key)
        if cached_analysis:
            self._update_conversation_state(cached_analysis)
            return cached_analysis

        # Perform incremental analysis
        analysis = {
            "new_requirements": self._extract_requirements(message),
            "new_topics": self._identify_topics(message),
            "confidence_updates": self._update_confidence(message),
            "missing_info": self._identify_missing_information(message, project_info)
        }

        # Update conversation state
        self._update_conversation_state(analysis)

        # Cache the analysis
        self.memory.cache.set("realtime_analysis", analysis, **cache_key)
        return analysis

    def _update_conversation_state(self, analysis: Dict[str, Any]) -> None:
        """Update the conversation state with new analysis."""
        self.conversation_state["requirements"].update(analysis["new_requirements"])
        self.conversation_state["identified_topics"].update(analysis["new_topics"])
        self.conversation_state["confidence_scores"].update(analysis["confidence_updates"])
        self.conversation_state["missing_information"].update(analysis["missing_info"])

    def _extract_requirements(self, message: Dict[str, str]) -> Dict[str, Any]:
        """Extract requirements from any type of user message."""
        prompt = f"""
        From the following message, identify any project requirements or important information.
        Group them naturally based on their content, without forcing them into predefined categories.
        
        Message: {message['content']}
        """
        
        requirements = self.llm.invoke(prompt)
        return {
            "identified_requirements": requirements.content,
            "confidence": requirements.additional_kwargs.get("confidence", 0.0)
        }

    def _identify_topics(self, message: Dict[str, str]) -> set:
        """Identify new topics from a message."""
        # Implementation would use category matching and topic extraction
        return set()

    def _update_confidence(self, message: Dict[str, str]) -> Dict[str, float]:
        """Update confidence scores for existing requirements."""
        # Implementation would assess confidence in current understanding
        return {}

    def _identify_missing_information(self, message: Dict[str, str], project_info: Dict[str, Any]) -> set:
        """Identify what information is still needed."""
        # Implementation would compare current state against required information
        return set()

    def progressive_outline_update(self, message: Dict[str, str], project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Update the RFP outline based on any new information."""
        current_outline = self.memory.get_state().get("current_outline", {})
        
        # Extract information without forcing categorization
        new_info = self._extract_requirements(message)
        
        # Dynamically update relevant sections based on content
        if new_info["identified_requirements"]:
            current_outline["requirements"] = current_outline.get("requirements", [])
            current_outline["requirements"].append({
                "content": new_info["identified_requirements"],
                "confidence": new_info["confidence"]
            })
        
        return {
            "outline": current_outline,
            "changes": new_info
        }

print("agent_interface.py 실행완료")