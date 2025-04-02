from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List, Dict
from langchain.chat_models import ChatOpenAI
import logging

logger = logging.getLogger(__name__)

class SectionSchema(BaseModel):
    id: str
    title: str
    relevance: float
    subsections: List[str]
    relevant_tasks: List[Dict]

class OutlineSchema(BaseModel):
    category: str
    language: str
    sections: List[SectionSchema]
    metadata: Dict

class OutlineChain:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=OutlineSchema)
        
        self.prompt = PromptTemplate(
            template="""다음 작업 결과를 바탕으로 RFP 개요를 생성해주세요:
            
            작업 결과: {task_result}
            카테고리: {categories}
            
            다음 형식으로 응답해주세요:
            {format_instructions}
            
            주의사항:
            1. 함수 호출이 아닌 직접 JSON 형식으로 응답해주세요.
            2. 응답은 반드시 유효한 JSON 형식이어야 합니다.
            3. 응답 앞뒤에 추가 텍스트를 넣지 마세요.
            4. 모든 필수 필드가 포함되어야 합니다.
            """,
            input_variables=["task_result", "categories"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser
        
    def invoke(self, task_result: Dict, categories: List[str]) -> Dict:
        """개요를 생성합니다."""
        try:
            # Get the raw response from the chain
            response = self.chain.invoke({
                "task_result": task_result,
                "categories": categories
            })
            
            # If it's a function call response, extract the arguments
            if hasattr(response, 'function_call') and response.function_call:
                import json
                try:
                    # Try to parse the function call arguments
                    return json.loads(response.function_call.arguments)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류: {str(e)}")
                    # If parsing fails, try to extract JSON from the content
                    content = response.function_call.arguments
                    # Remove any markdown code blocks
                    content = content.replace('```json', '').replace('```', '').strip()
                    return json.loads(content)
            
            # If it's already a dict, return it
            if isinstance(response, dict):
                return response
                
            # If it's a Pydantic model, convert to dict
            if hasattr(response, 'model_dump'):
                return response.model_dump()
                
            # If it's a string, try to parse it as JSON
            if isinstance(response, str):
                import json
                # Remove any markdown code blocks
                response = response.replace('```json', '').replace('```', '').strip()
                return json.loads(response)
                
            raise ValueError(f"Unexpected response type: {type(response)}")
            
        except Exception as e:
            logger.error(f"개요 생성 중 오류 발생: {str(e)}")
            raise

def create_outline_chain() -> OutlineChain:
    """개요 생성 체인을 생성합니다."""
    return OutlineChain()