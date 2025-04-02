# agent/core/integration.py
from ..memory.memory_system import MemorySystem
from ..memory.memory_state import AgentState
from typing import Dict
from .category_chain import CategoryChain
from .task_chain import create_task_chain
from .outline_chain import create_outline_chain

class AgentCore:
    def __init__(self):
        self.memory = MemorySystem()
        self.category_chain = CategoryChain()
        self.task_chain = create_task_chain()
        self.outline_chain = create_outline_chain()
        
    async def process_request(self, request: str) -> Dict:
        # 현재 상태 가져오기
        state = self.memory.get_state()
        
        # 카테고리 매칭
        categories = self.category_chain.match_categories(request)
        
        # 작업 분해
        tasks = await self.task_chain.arun(
            request=request,
            state=state
        )
        
        # 현재 작업 설정
        self.memory.set_current_task(tasks[0] if tasks else {})
        
        # 개요 생성
        outline = await self.outline_chain.arun(
            tasks=tasks,
            category=categories[0]["category"] if categories else "",
            state=state
        )
        
        # 상호작용 저장
        self.memory.add_interaction({
            "request": request,
            "categories": categories,
            "tasks": tasks,
            "outline": outline
        })
        
        return {
            "categories": categories,
            "tasks": tasks,
            "outline": outline,
            "state": state
        }