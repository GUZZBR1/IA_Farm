"""Compatibility adapter for the single local vector database implementation."""

from typing import Any, Dict, List, Optional

from tools.vector_db import LocalVectorDB


class VectorEngine:
    """Backward-compatible facade over :class:`LocalVectorDB`.

    ``api_key`` is accepted for callers from the previous remote-embedding
    prototype, but is intentionally unused. Retrieval stays local and the
    OpenRouter credential is never required to build an index.
    """

    def __init__(self, api_key: Optional[str] = None, index_path: str = "data/vector_index"):
        self.db = LocalVectorDB(index_path=index_path)

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        self.db.index_documents(documents)

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        return self.db.query(query, k=k)

    def save(self) -> None:
        """Preserve the old API; LocalVectorDB saves during indexing."""

        return None
