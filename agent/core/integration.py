from typing import Dict, List
from .task_chain import create_task_chain
from .outline_chain import create_outline_chain
from .category_chain import CategoryChain

class AgentCore:
    def __init__(self):
        self.task_chain = create_task_chain()
        self.outline_chain = create_outline_chain()
        self.category_chain = CategoryChain()
        
    async def process_request(self, request: str) -> Dict:
        # 1. Category Matching (Hybrid)
        categories = self.category_chain.match_categories(request)
        
        # 2. Task Decomposition (LangChain)
        tasks = await self.task_chain.arun(
            request=request,
            context={"categories": categories}
        )
        
        # 3. Outline Generation (LangChain)
        outline = await self.outline_chain.arun(
            tasks=tasks,
            category=categories[0]["category"],
            rag_results=[]  # Get from RAG pipeline
        )
        
        return {
            "categories": categories,
            "tasks": tasks,
            "outline": outline
        }