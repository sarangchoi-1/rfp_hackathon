# agent/memory/memory_system.py
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json
from .memory_state import AgentState
from utils.logger import Logger
from .cache_system import CacheSystem

class MemorySystem:
    """
    통합 메모리 시스템
    AgentState를 사용하여 모든 메모리 관리
    """
    
    def __init__(self):
        self.logger = Logger(__name__)       
        self.cache = CacheSystem()
        self.state: AgentState = {
            "patterns": {},
            "recent_context": [],
            "current_task": {},
            "rag_results": [],
            "timestamp": datetime.now().timestamp(),
            "metadata": {}
        }
        
        # 파일 저장 경로
        self.storage_path = Path("data/memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 상태 로드
        self._load_state()
        
        
    def save_pattern(self, pattern_key: str, pattern_data: Dict) -> bool:
        """장기 패턴 저장"""
        try:
            self.state["patterns"][pattern_key] = {
                **pattern_data,
                "timestamp": datetime.now().timestamp()
            }
            self._save_state()
            return True
        except Exception as e:
            self.logger.log_error(f"패턴 저장 실패: {str(e)}")
            return False
            
    def add_interaction(self, interaction: Dict) -> bool:
        """최근 컨텍스트에 상호작용 추가"""
        try:
            self.state["recent_context"].append({
                **interaction,
                "timestamp": datetime.now().timestamp()
            })
            
            # 최근 컨텍스트 크기 제한 (예: 최근 100개)
            if len(self.state["recent_context"]) > 100:
                self.state["recent_context"] = self.state["recent_context"][-100:]
                
            self._save_state()
            return True
        except Exception as e:
            self.logger.log_error(f"상호작용 추가 실패: {str(e)}")
            return False
            
    def set_current_task(self, task: Dict) -> bool:
        """현재 작업 상태 설정"""
        try:
            self.state["current_task"] = {
                **task,
                "timestamp": datetime.now().timestamp()
            }
            self._save_state()
            return True
        except Exception as e:
            self.logger.log_error(f"작업 상태 설정 실패: {str(e)}")
            return False
            
    def update_rag_results(self, results: List[Dict]) -> bool:
        """RAG 파이프라인 결과 업데이트"""
        try:
            self.state["rag_results"] = results
            self.state["timestamp"] = datetime.now().timestamp()
            self._save_state()
            return True
        except Exception as e:
            self.logger.log_error(f"RAG 결과 업데이트 실패: {str(e)}")
            return False
            
    def get_state(self) -> AgentState:
        """현재 상태 조회"""
        return self.state
        
    def _save_state(self):
        """상태를 파일에 저장"""
        try:
            state_file = self.storage_path / "agent_state.json"
            with state_file.open("w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.log_error(f"상태 저장 실패: {str(e)}")
            
    def _load_state(self):
        """파일에서 상태 로드"""
        try:
            state_file = self.storage_path / "agent_state.json"
            if state_file.exists():
                with state_file.open("r", encoding="utf-8") as f:
                    loaded_state = json.load(f)
                    self.state.update(loaded_state)
        except Exception as e:
            self.logger.log_error(f"상태 로드 실패: {str(e)}")
    
    def clear_state(self) -> None:
        """상태 초기화"""
        try:
            self.state = {
                "patterns": {},
                "recent_context": [],
                "current_task": {},
                "rag_results": [],
                "timestamp": datetime.now().timestamp(),
                "metadata": {
                    "version": "1.0",
                    "last_cleanup": datetime.now().timestamp()
                }
            }
            self._save_state()
            self.logger.log_info("State cleared successfully")
        except Exception as e:
            self.logger.log_error(f"Error clearing state: {str(e)}")