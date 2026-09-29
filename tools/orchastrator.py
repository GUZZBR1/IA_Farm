"""Deterministic orchestration between metadata, retrieval and curated references."""

import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from tools.metadata import canonicalize
from tools.vector_db import LocalVectorDB


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NO_CONTEXT_RESPONSE = (
    "I do not have validated technical data for this query and context. "
    "Please provide the region, climate and crop details."
)
TECHNICAL_KEYWORDS = (
    "dosage", "dosagem", "dosagens", "dose", "amount", "how much", "quanto", "quantidade", "kg/ha",
    "l/ha", "apply", "aplicar", "treatment", "tratamento", "fertilizer", "adubo",
    "fertilizante", "pesticide", "pesticida", "fungicide", "fungicida", "npk",
    "inseticida", "herbicida", "agrotoxico", "defensivo", "veneno", "pulverizar",
    "chemical control", "controle quimico", "chemical", "treat", "recomendacao",
    "recommendation", "agroquimico", "aplicacao",
    "pest control", "controle de pragas", "manejo de pragas",
    "tratar", "quimico",
)
REGION_ALIASES = (
    "mato grosso", "mt", "cerrado", "minas gerais", "mg", "parana", "pr",
    "sao paulo", "sp", "bahia", "ba",
)
CLIMATE_ALIASES = (
    "tropical", "equatorial", "semiarido", "semi-arido", "subtropical",
    "temperate", "temperado", "arid", "arido",
)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = _normalize_text(phrase)
    return bool(re.search(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)", _normalize_text(text)))


class Orchestrator:
    def __init__(self, vector_db_path: Optional[str] = None, db=None):
        default_index_path = PROJECT_ROOT / "data" / "vector_index"
        self.db = db if db is not None else LocalVectorDB(
            index_path=str(vector_db_path or default_index_path)
        )
        self.required_metadata = ["region", "climate"]

    def _extract_metadata(self, user_input: str) -> Dict[str, str]:
        """Extract only explicit, deterministic region/climate mentions."""

        extracted: Dict[str, str] = {}
        for alias in REGION_ALIASES:
            if _contains_phrase(user_input, alias):
                extracted["region"] = canonicalize("region", alias)
                break
        for alias in CLIMATE_ALIASES:
            if _contains_phrase(user_input, alias):
                extracted["climate"] = canonicalize("climate", alias)
                break
        return extracted

    @staticmethod
    def _is_technical_request(user_input: str) -> bool:
        normalized = _normalize_text(user_input)
        if re.search(r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:kg|g|mg|l|ml)/ha\b", normalized):
            return True
        for keyword in TECHNICAL_KEYWORDS:
            if _contains_phrase(normalized, keyword):
                return True
        return False

    def rag_query(self, query: str, context_filters: Optional[Dict[str, Any]] = None) -> str:
        """Return reviewed source excerpts without generating or inferring advice."""
        docs = self.db.query(query, filters=context_filters)
        reviewed_docs = [document for document in docs if self._is_reviewed(document)]
        if not reviewed_docs:
            return NO_CONTEXT_RESPONSE

        excerpts = []
        for document in reviewed_docs:
            text = str(document.get("text", "")).strip()
            metadata = document.get("metadata", document)
            source = metadata.get("source_id") or metadata.get("source")
            if text and source:
                excerpts.append(f"Source: {source}\n{text}")

        if not excerpts:
            return NO_CONTEXT_RESPONSE

        return (
            "Validated local references (shown verbatim):\n\n"
            + "\n\n---\n\n".join(excerpts)
        )

    @staticmethod
    def _is_reviewed(document: Dict[str, Any]) -> bool:
        """Require provenance and explicit agronomist review before displaying data."""
        if not isinstance(document, dict):
            return False
        # LocalVectorDB stores metadata fields beside `text`; fixtures and
        # ingestion APIs may instead wrap them under `metadata`.
        metadata = document.get("metadata", document)
        if not isinstance(metadata, dict) or not str(document.get("text", "")).strip():
            return False
        status = str(metadata.get("review_status", "")).casefold()
        source = metadata.get("source_id") or metadata.get("source")
        reviewed_at = metadata.get("reviewed_at") or metadata.get("review_date")
        if status not in {"approved", "validated"} or not source or not reviewed_at:
            return False
        try:
            review_date = date.fromisoformat(str(reviewed_at))
        except ValueError:
            return False
        return review_date <= date.today()

    def handle_request(self, user_input: str, session_state: Dict[str, Any]) -> str:
        """Require region and climate before technical recommendations."""

        session_state.update(self._extract_metadata(user_input))
        if not self._is_technical_request(user_input):
            return self.rag_query(user_input)

        normalized_state = {
            key: canonicalize(key, value)
            for key, value in session_state.items()
        }
        missing = [key for key in self.required_metadata if not normalized_state.get(key)]
        if missing:
            return (
                "To provide an accurate dosage, I need more information. "
                f"Please tell me your {', '.join(missing)}."
            )

        filters = {key: normalized_state[key] for key in self.required_metadata}
        return self.rag_query(user_input, context_filters=filters)


def main() -> None:
    orch = Orchestrator()
    session_state: Dict[str, Any] = {}
    print("--- IA_Farm Guided Interface ---")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nUser: ")
        except EOFError:
            break

        if user_input.casefold() in {"exit", "quit"}:
            break

        response = orch.handle_request(user_input, session_state)
        print(f"AI: {response}")


if __name__ == "__main__":
    main()
