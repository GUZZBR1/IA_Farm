"""Small structural contracts shared by application code and adapters."""

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any, Protocol, runtime_checkable


RequestState = MutableMapping[str, Any]
CandidateDocument = Mapping[str, Any]


@runtime_checkable
class VectorRetriever(Protocol):
    """Minimum retrieval interface required by the application orchestrator."""

    def query(
        self,
        query_text: str,
        /,
        filters: Mapping[str, Any] | None = None,
    ) -> Sequence[CandidateDocument]: ...
