# utils/models.py
from typing import TypedDict, List, Dict, Optional
from datetime import datetime

class Document(TypedDict):
    """Shared document structure across all components"""
    id: str
    content: str
    category: str  # research_papers/industry_rfps/best_practices/evaluation_methods
    metadata: Dict
    embedding: Optional[List[float]]
    created_at: datetime
    updated_at: datetime

class Task(TypedDict):
    """Shared task structure between Agent and RAG Pipeline"""
    id: str
    type: str  # purpose/scope/case/evaluation
    description: str
    priority: int
    dependencies: List[str]
    status: str  # pending/processing/completed/failed
    result: Optional[str]

class SearchResult(TypedDict):
    """Shared search result structure"""
    document: Document
    score: float
    relevance: float
    context: str