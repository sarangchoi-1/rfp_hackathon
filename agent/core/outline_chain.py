from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List, Dict

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

def create_outline_chain():
    prompt = PromptTemplate(
        input_variables=["tasks", "category", "rag_results"],
        template="""Generate an outline for:
        Tasks: {tasks}
        Category: {category}
        RAG Results: {rag_results}
        
        Consider domain-specific sections and maintain proper structure.
        """
    )
    
    output_parser = PydanticOutputParser(pydantic_object=OutlineSchema)
    
    return LLMChain(
        llm=ChatOpenAI(),
        prompt=prompt,
        output_parser=output_parser
    )