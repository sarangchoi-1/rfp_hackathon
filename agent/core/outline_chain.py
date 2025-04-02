from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List, Dict
from langchain.chat_models import ChatOpenAI

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
            """,
            input_variables=["task_result", "categories"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm | self.parser
        
    def invoke(self, task_result: Dict, categories: List[str]) -> Dict:
        """개요를 생성합니다."""
        return self.chain.invoke({
            "task_result": task_result,
            "categories": categories
        })

def create_outline_chain() -> OutlineChain:
    """개요 생성 체인을 생성합니다."""
    return OutlineChain()