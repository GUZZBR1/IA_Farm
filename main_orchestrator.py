"""Compatibility entry point backed by the production orchestrator."""

from typing import Any, Dict, Optional

from tools.memory_manager import MemoryManager
from tools.orchastrator import Orchestrator


class AgriBrainOrchestrator:
    """Expose the newer ``handle_query`` API without a second RAG pipeline."""

    def __init__(self, api_key: Optional[str] = None, vector_db_path: Optional[str] = None, db=None):
        self.mem = MemoryManager()
        self.orchestrator = Orchestrator(vector_db_path=vector_db_path, db=db)

    def handle_query(self, query: str, session_state: Optional[Dict[str, Any]] = None) -> str:
        state = session_state if session_state is not None else {}
        response = self.orchestrator.handle_request(query, state)
        self.mem.add_interaction(query, response, metadata=state)
        return response


if __name__ == "__main__":
    print("Use `python main.py` for the interactive interface.")
