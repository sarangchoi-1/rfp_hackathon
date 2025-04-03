from typing import Dict, List, Optional
from pydantic import BaseModel

class AgentState(BaseModel):
    current_request: Optional[str] = None
    categories: List[Dict] = []
    tasks: List[Dict] = []
    outline: Optional[Dict] = None
    rag_results: List[Dict] = []
    memory_context: Dict = {}