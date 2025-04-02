# agent/memory/state.py
from typing import Dict, List, TypedDict, Optional
from datetime import datetime

class AgentState(TypedDict):
    """
    통합된 에이전트 상태 관리
    모든 메모리 컴포넌트를 하나의 상태로 통합
    """
    patterns: Dict[str, Dict]      # Long-term patterns
    recent_context: List[Dict]     # Short-term context
    current_task: Dict            # Working memory
    rag_results: List[Dict]       # RAG pipeline results
    timestamp: float              # Last update timestamp
    metadata: Dict                # Additional metadata