from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List, Dict
from langchain.chat_models import ChatOpenAI

class TaskSchema(BaseModel):
    task_id: str
    task_type: str
    description: str
    priority: int
    dependencies: List[str]

def create_task_chain():
    prompt = PromptTemplate(
        input_variables=["request", "context"],
        template="""다음 요청을 구조화된 작업으로 분해해주세요:
        요청: {request}
        맥락: {context}
        
        다음 사항들을 고려해주세요:
        1. 목적 분석
           - 요청의 핵심 목적은 무엇인가?
           - 어떤 문제를 해결하려 하는가?
           - 최종 목표는 무엇인가?
        
        2. 범위 정의
           - 어떤 기능들이 필요한가?
           - 어떤 제약사항이 있는가?
           - 어떤 리소스가 필요한가?
        
        3. 사례 연구
           - 유사한 사례가 있는가?
           - 어떤 접근 방식이 효과적이었는가?
           - 어떤 실패 사례가 있는가?
        
        4. 평가 기준
           - 성공의 기준은 무엇인가?
           - 어떤 지표로 평가할 것인가?
           - 품질 기준은 무엇인가?
        
        출력은 우선순위와 의존성이 포함된 구조화된 작업이어야 합니다.
        각 작업은 고유한 ID를 가지고 있어야 하며, 다른 작업과의 의존 관계를 명확히 표시해야 합니다.
        우선순위는 1(가장 높음)부터 5(가장 낮음)까지 지정해주세요.
        """
    )
    
    output_parser = PydanticOutputParser(pydantic_object=TaskSchema)
    
    return LLMChain(
        llm=ChatOpenAI(),
        prompt=prompt,
        output_parser=output_parser
    )