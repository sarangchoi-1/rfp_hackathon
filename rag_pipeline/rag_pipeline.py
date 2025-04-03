import os
import json
import requests
from typing import List
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from langchain.schema import Document
from data.Retrieve import double_retrieve

env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

class RAGPipeline:
    def __init__(self, memory_system):
        self.memory = memory_system
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
    def rag_pipeline(self, context: List[str], query: str) -> str:
        # Try cache first
        cached_result = self.memory.cache.get(
            "rag_result",
            context=context,
            query=query
        )
        if cached_result:
            return cached_result

        # Generate response if not cached
        context_text = "\n".join(context)
        prompt = f"""
        다음 문서는 신뢰도 높은 공식적인 문서다.
        이를 참고하고, 반드시 문서에만 근거해서 답변한다.

        문서:
        {context_text}

        질문:
        {query}
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """너는 문서를 기반으로 응답하는 시스템이다. 오직 제공된 문서 내용만 사용해서 대답한다. 
                 문서에 나오는 고유명사와 정보는 신뢰할 수 있으며, 활용해야 한다. 
                 또한 답변은 html과 css 형식으로 작성해야 한다.
                 """},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        result = response.choices[0].message.content.strip()
        
        # Cache the result
        self.memory.cache.set(
            "rag_result",
            result,
            context=context,
            query=query
        )
        return result

def retrieve_documents(self, query: str) -> List[Document]:
    """Document retrieval with caching."""
    cached_docs = self.memory.cache.get(
        "retrieved_docs",
        query=query
    )
    if cached_docs:
        return cached_docs

    docs = self.vectorstore.similarity_search(query)
    
    self.memory.cache.set(
        "retrieved_docs",
        docs,
        query=query
    )
    return docs
