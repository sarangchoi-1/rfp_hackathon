from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List, Dict

class TaskSchema(BaseModel):
    task_id: str
    task_type: str
    description: str
    priority: int
    dependencies: List[str]

def create_task_chain():
    prompt = PromptTemplate(
        input_variables=["request", "context"],
        template="""Decompose the following request into structured tasks:
        Request: {request}
        Context: {context}
        
        Consider:
        1. Purpose analysis
        2. Scope definition
        3. Case studies
        4. Evaluation criteria
        
        Output should be structured tasks with priorities and dependencies.
        """
    )
    
    output_parser = PydanticOutputParser(pydantic_object=TaskSchema)
    
    return LLMChain(
        llm=ChatOpenAI(),
        prompt=prompt,
        output_parser=output_parser
    )