import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env'))

# Initialize OpenAI with API key from environment
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables")

class PurposeAnalysis(BaseModel):
    core_purpose: str = Field(description="프로젝트의 핵심 목적")
    problem_statement: str = Field(description="해결하고자 하는 문제 진술")
    final_goal: str = Field(description="프로젝트의 최종 목표")
    key_objectives: List[str] = Field(description="주요 목표들의 리스트")
    next_topic: str = Field(description="다음으로 다룰 주제")
    conversation_context: str = Field(description="대화의 주요 맥락")
    extracted_info: Dict[str, Any] = Field(description="추출된 정보")
    missing_info: List[str] = Field(description="누락된 정보 목록")

class ScopeDefinition(BaseModel):
    required_features: List[str] = Field(description="필요한 기능들의 리스트")
    constraints: List[str] = Field(description="제약사항들의 리스트")
    required_resources: List[str] = Field(description="필요한 리소스들의 리스트")
    timeline_estimates: Dict[str, str] = Field(description="단계별 예상 소요 시간")

class CaseStudy(BaseModel):
    similar_cases: List[str] = Field(description="유사 사례들의 리스트")
    effective_approaches: List[str] = Field(description="효과적인 접근 방식들의 리스트")
    failure_cases: List[str] = Field(description="실패 사례들의 리스트")
    lessons_learned: List[str] = Field(description="교훈들의 리스트")

class EvaluationCriteria(BaseModel):
    success_metrics: List[str] = Field(description="성공 지표들의 리스트")
    quality_standards: List[str] = Field(description="품질 기준들의 리스트")
    performance_indicators: List[str] = Field(description="성과 지표들의 리스트")

class TaskSchema(BaseModel):
    task_id: str = Field(description="작업의 고유 ID")
    task_type: str = Field(description="작업의 유형")
    description: str = Field(description="작업의 상세 설명")
    priority: int = Field(description="우선순위 (1-5)")
    dependencies: List[str] = Field(description="의존성 있는 작업들의 ID 리스트")

def create_purpose_analysis_chain():
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing project purposes and objectives.
        Your task is to analyze the given request and context to identify the core purpose, problem statement, final goal, and key objectives.
        Also analyze the conversation to determine the next topic and extract relevant information.
        Provide your response in a structured format matching the required schema."""),
        ("human", """다음 요청의 목적을 분석해주세요:
        요청: {request}
        맥락: {context}
        
        다음 사항들을 분석해주세요:
        1. 핵심 목적 (core_purpose)
        2. 문제 진술 (problem_statement)
        3. 최종 목표 (final_goal)
        4. 주요 목표들 (key_objectives)
        5. 다음 주제 (next_topic)
        6. 대화 맥락 (conversation_context)
        7. 추출된 정보 (extracted_info)
        8. 누락된 정보 (missing_info)
        
        각 항목에 대해 구체적이고 명확한 설명을 제공해주세요.""")
    ])
    
    chain = prompt | llm.bind(functions=[{
        "name": "analyze_purpose",
        "description": "Analyze project purpose and objectives",
        "parameters": {
            "type": "object",
            "properties": {
                "core_purpose": {"type": "string"},
                "problem_statement": {"type": "string"},
                "final_goal": {"type": "string"},
                "key_objectives": {"type": "array", "items": {"type": "string"}},
                "next_topic": {"type": "string"},
                "conversation_context": {"type": "string"},
                "extracted_info": {"type": "object"},
                "missing_info": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["core_purpose", "problem_statement", "final_goal", "key_objectives", 
                        "next_topic", "conversation_context", "extracted_info", "missing_info"]
        }
    }])
    return chain

def create_scope_definition_chain():
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at defining project scope and requirements.
        Your task is to analyze the given request, context, and purpose analysis to define the project scope.
        Make sure to include timeline estimates for each major phase of the project.
        Provide your response in a structured format matching the required schema."""),
        ("human", """다음 요청의 범위를 정의해주세요:
        요청: {request}
        맥락: {context}
        목적 분석: {purpose_analysis}
        
        다음 사항들을 포함해주세요:
        1. 필요한 기능들 (required_features)
        2. 제약사항들 (constraints)
        3. 필요한 리소스들 (required_resources)
        4. 단계별 예상 소요 시간 (timeline_estimates) - 각 주요 단계별 예상 소요 시간을 지정해주세요.""")
    ])
    
    chain = prompt | llm.bind(functions=[{
        "name": "define_scope",
        "description": "Define project scope and requirements",
        "parameters": {
            "type": "object",
            "properties": {
                "required_features": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
                "required_resources": {"type": "array", "items": {"type": "string"}},
                "timeline_estimates": {"type": "object"}
            },
            "required": ["required_features", "constraints", "required_resources", "timeline_estimates"]
        }
    }])
    return chain

def create_case_study_chain():
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing project case studies and lessons learned.
        Your task is to analyze the given request and identify relevant cases.
        Provide your response in a structured format matching the required schema."""),
        ("human", """다음 요청과 관련된 사례를 연구해주세요:
        요청: {request}
        맥락: {context}
        목적 분석: {purpose_analysis}
        범위 정의: {scope_definition}""")
    ])
    
    chain = prompt | llm.bind(functions=[{
        "name": "analyze_cases",
        "description": "Analyze project case studies",
        "parameters": {
            "type": "object",
            "properties": {
                "similar_cases": {"type": "array", "items": {"type": "string"}},
                "effective_approaches": {"type": "array", "items": {"type": "string"}},
                "failure_cases": {"type": "array", "items": {"type": "string"}},
                "lessons_learned": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["similar_cases", "effective_approaches", "failure_cases", "lessons_learned"]
        }
    }])
    return chain

def create_evaluation_criteria_chain():
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at defining project evaluation criteria.
        Your task is to analyze the given information and define evaluation criteria.
        Provide your response in a structured format matching the required schema."""),
        ("human", """다음 요청의 평가 기준을 정의해주세요:
        요청: {request}
        맥락: {context}
        목적 분석: {purpose_analysis}
        범위 정의: {scope_definition}
        사례 연구: {case_study}""")
    ])
    
    chain = prompt | llm.bind(functions=[{
        "name": "define_criteria",
        "description": "Define project evaluation criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "success_metrics": {"type": "array", "items": {"type": "string"}},
                "quality_standards": {"type": "array", "items": {"type": "string"}},
                "performance_indicators": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["success_metrics", "quality_standards", "performance_indicators"]
        }
    }])
    return chain

def create_task_chain():
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at breaking down projects into structured tasks.
        Your task is to analyze the given information and create structured tasks.
        Provide your response in a structured format matching the required schema."""),
        ("human", """다음 분석 결과를 바탕으로 구조화된 작업을 생성해주세요:
        요청: {request}
        맥락: {context}
        목적 분석: {purpose_analysis}
        범위 정의: {scope_definition}
        사례 연구: {case_study}
        평가 기준: {evaluation_criteria}""")
    ])
    
    chain = prompt | llm.bind(functions=[{
        "name": "create_tasks",
        "description": "Create structured project tasks",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "task_type": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "integer"},
                "dependencies": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["task_id", "task_type", "description", "priority", "dependencies"]
        }
    }])
    return chain

# 각 답변에 대해 html 형식으로 출력해주세요.