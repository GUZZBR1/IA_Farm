"""Deterministic orchestration between metadata, retrieval and curated references."""

import re
import unicodedata
from datetime import date
from pathlib import Path
import os
from typing import Any, Dict, Optional

from tools.metadata import canonicalize
from tools.curation_registry import CurationRegistry
from tools.contracts import RequestState, VectorRetriever
from tools.vector_db import LocalVectorDB


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NO_CONTEXT_RESPONSE = (
    "Não encontrei uma fonte técnica aprovada para esta pergunta e contexto. "
    "Não vou inferir uma recomendação. Informe os detalhes relevantes ou "
    "consulte um profissional habilitado."
)
REFERENCE_HEADER = (
    "Trechos de fontes locais com revisão registrada "
    "(exibidos literalmente; não constituem recomendação):"
)
TECHNICAL_KEYWORDS = (
    "dosage", "dosagem", "dosagens", "dose", "amount", "how much", "quanto", "quantidade", "kg/ha",
    "l/ha", "apply", "aplicar", "treatment", "tratamento", "fertilizer", "adubo",
    "fertilizante", "pesticide", "pesticida", "fungicide", "fungicida", "npk",
    "inseticida", "herbicida", "agrotoxico", "defensivo", "veneno", "pulverizar",
    "chemical control", "controle quimico", "chemical", "treat", "recomendacao",
    "recommendation", "agroquimico", "aplicacao",
    "pest control", "controle de pragas", "manejo de pragas",
    "tratar", "quimico", "adubacao", "lagarta", "cigarrinha", "plantio",
    "semeadura", "doenca", "sintoma", "sintomas", "recomendado", "recomendada",
    # Common field descriptions must not fall through to an unscoped search.
    "milho", "milhos", "maize", "corn", "lavoura", "roca", "folha", "folhas",
    "planta", "plantas", "solo", "safra", "cultivar", "irrigacao", "irrigar",
    "amarela", "amarelo", "amarelas", "amarelos", "roxo", "roxa", "mancha",
    "murcha", "murchando", "enrolada", "enrolamento", "espiga", "grao", "graos",
    "daninha", "daninhas", "ervas daninhas",
)
REGION_ALIASES = (
    "mato grosso", "mt", "cerrado", "minas gerais", "mg", "parana", "pr",
    "sao paulo", "sp", "bahia", "ba",
)
CLIMATE_ALIASES = (
    "tropical", "equatorial", "semiarido", "semi-arido", "semi arido", "subtropical",
    "temperate", "temperado", "arid", "arido",
)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = _normalize_text(phrase)
    return bool(re.search(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)", _normalize_text(text)))


def _last_explicit_alias(text: str, aliases: tuple[str, ...], negation: str) -> Optional[str]:
    """Return the last affirmative alias, ignoring directly negated mentions."""

    normalized = _normalize_text(text)
    mentions = []
    for alias in aliases:
        phrase = _normalize_text(alias)
        pattern = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)")
        for match in pattern.finditer(normalized):
            mentions.append((match.start(), match.end(), alias, len(phrase)))

    # Prefer a compound alias over a shorter alias contained inside it,
    # e.g. "semi árido" over its final word "árido".
    explicit_mentions = [
        mention for mention in mentions
        if not any(
            other[0] <= mention[0]
            and mention[1] <= other[1]
            and other[3] > mention[3]
            for other in mentions
        )
    ]
    affirmative = []
    for start, end, alias, _ in explicit_mentions:
        prefix = normalized[max(0, start - 48):start]
        if not re.search(negation, prefix):
            affirmative.append((start, end, alias))
    return max(affirmative, default=(0, 0, None), key=lambda item: item[0])[2]


def _has_negated_alias(text: str, aliases: tuple[str, ...], negation: str) -> bool:
    """Whether the message explicitly denies any known metadata alias."""

    normalized = _normalize_text(text)
    for alias in aliases:
        phrase = _normalize_text(alias)
        pattern = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)")
        for match in pattern.finditer(normalized):
            prefix = normalized[max(0, match.start() - 48):match.start()]
            if re.search(negation, prefix):
                return True
    return False


def _has_ambiguous_alternative(text: str, aliases: tuple[str, ...]) -> bool:
    """Detect distinct region aliases explicitly presented as alternatives."""

    normalized = _normalize_text(text)
    mentions = []
    for alias in aliases:
        phrase = _normalize_text(alias)
        pattern = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)")
        for match in pattern.finditer(normalized):
            mentions.append((match.start(), match.end(), canonicalize("region", alias)))
    mentions.sort()
    for index, (left, right) in enumerate(zip(mentions, mentions[1:])):
        if left[2] != right[2] and re.search(r"\b(?:ou|or)\b", normalized[left[1]:right[0]]):
            correction = re.search(
                r"\b(?:corrigindo|na verdade|quer dizer|actually|correction)\b",
                normalized[right[1]:],
            )
            if correction:
                correction_position = right[1] + correction.start()
                if any(start > correction_position for start, _, _ in mentions[index + 2:]):
                    continue
            return True
    return False


class Orchestrator:
    def __init__(
        self,
        vector_db_path: Optional[str] = None,
        db: Optional[VectorRetriever] = None,
        curation_registry=None,
        embedding_model_path: Optional[str] = None,
        embedding_model_id: Optional[str] = None,
        embedding_model_revision: Optional[str] = None,
        expected_knowledge_release: Optional[str] = None,
    ):
        default_index_path = PROJECT_ROOT / "data" / "vector_index"
        self.db = db if db is not None else LocalVectorDB(
            index_path=str(vector_db_path or default_index_path),
            model_name=(embedding_model_path or os.environ.get("IA_FARM_EMBEDDING_MODEL_PATH", "")),
            model_id=(embedding_model_id or os.environ.get("IA_FARM_EMBEDDING_MODEL_ID")),
            model_revision=(embedding_model_revision or os.environ.get("IA_FARM_EMBEDDING_MODEL_REVISION")),
            expected_release_id=(expected_knowledge_release or os.environ.get("IA_FARM_KNOWLEDGE_RELEASE")),
        )
        self.required_metadata = ["region", "climate"]
        self.curation_registry = curation_registry or CurationRegistry(
            PROJECT_ROOT / "data" / "curation_registry.json"
        )

    def _extract_metadata(self, user_input: str) -> Dict[str, str]:
        """Extract the last affirmative, deterministic region/climate mention."""

        extracted: Dict[str, str] = {}
        ambiguous_region = _has_ambiguous_alternative(user_input, REGION_ALIASES)
        if ambiguous_region:
            # An either/or invalidates stale region context, but independent
            # fields (such as an explicit climate) should still be extracted.
            extracted["region"] = ""
        else:
            region = _last_explicit_alias(
                user_input,
                REGION_ALIASES,
                r"\b(?:nao\s+(?:estou|moro|fico|sou)\s+(?:mais\s+)?(?:em|no|na)|not\s+(?:located\s+)?in)\s*$",
            )
            if region:
                extracted["region"] = canonicalize("region", region)
            elif _has_negated_alias(
                user_input,
                REGION_ALIASES,
                r"\b(?:nao\s+(?:estou|moro|fico|sou)\s+(?:mais\s+)?(?:em|no|na)|not\s+(?:located\s+)?in)\s*$",
            ):
                extracted["region"] = ""
        climate = _last_explicit_alias(
            user_input,
            CLIMATE_ALIASES,
            r"\b(?:nao\s+(?:e|eh)|not)\s*$",
        )
        if climate:
            extracted["climate"] = canonicalize("climate", climate)
        elif _has_negated_alias(
            user_input,
            CLIMATE_ALIASES,
            r"\b(?:nao\s+(?:e|eh)|not)\s*$",
        ):
            extracted["climate"] = ""
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
        reviewed_docs = [
            document for document in docs
            if self._is_reviewed(document)
            and self._matches_context(document, context_filters or {})
        ]
        if not reviewed_docs:
            return NO_CONTEXT_RESPONSE

        excerpts = []
        for document in reviewed_docs:
            text = str(document.get("text", "")).strip()
            metadata = document.get("metadata", document)
            source = metadata.get("source_id") or metadata.get("source")
            if text and source:
                excerpts.append(f"Fonte: {source}\n{text}")

        if not excerpts:
            return NO_CONTEXT_RESPONSE

        return (
            f"{REFERENCE_HEADER}\n\n"
            + "\n\n---\n\n".join(excerpts)
        )

    def _is_reviewed(self, document: Dict[str, Any]) -> bool:
        """Require metadata plus an exact entry in the trusted curation registry."""
        if not self._has_review_metadata(document):
            return False
        return self.curation_registry.authorizes(document)

    @staticmethod
    def _has_review_metadata(document: Dict[str, Any]) -> bool:
        """Check display metadata only; this is not a production approval gate."""
        if not isinstance(document, dict):
            return False
        # LocalVectorDB stores metadata fields beside `text`; fixtures and
        # ingestion APIs may instead wrap them under `metadata`.
        metadata = document.get("metadata", document)
        if not isinstance(metadata, dict) or not str(document.get("text", "")).strip():
            return False
        crop = _normalize_text(str(metadata.get("crop", "")).strip())
        if crop not in {"maize", "corn", "milho"}:
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

    @staticmethod
    def _matches_context(
        document: Dict[str, Any], context_filters: Dict[str, Any]
    ) -> bool:
        """Never display region/climate-scoped evidence outside known scope."""
        metadata = document.get("metadata", document)
        if not isinstance(metadata, dict):
            return False
        neutral_scope = {"", "general", "global", "all", "any", "*"}
        for key in ("region", "climate"):
            actual = metadata.get(key)
            if actual is None or str(actual).strip().casefold() in neutral_scope:
                continue
            expected = context_filters.get(key)
            if expected is None or canonicalize(key, actual) != canonicalize(key, expected):
                return False
        return True

    def handle_request(self, user_input: str, session_state: RequestState) -> str:
        """Require region and climate before technical recommendations."""

        session_state.update(self._extract_metadata(user_input))
        if not self._is_technical_request(user_input):
            normalized_state = {
                key: canonicalize(key, value)
                for key, value in session_state.items()
                if key in self.required_metadata and value
            }
            return self.rag_query(user_input, context_filters=normalized_state or None)

        normalized_state = {
            key: canonicalize(key, value)
            for key, value in session_state.items()
        }
        missing = [key for key in self.required_metadata if not normalized_state.get(key)]
        if missing:
            labels = {"region": "região da propriedade", "climate": "clima local"}
            requested = [labels.get(key, key) for key in missing]
            return (
                "Para consultar uma fonte técnica com segurança, preciso de mais "
                f"informações: informe {', '.join(requested)}."
            )

        filters = {key: normalized_state[key] for key in self.required_metadata}
        return self.rag_query(user_input, context_filters=filters)


def main() -> None:
    orch = Orchestrator()
    session_state: Dict[str, Any] = {}
    print("--- IA_Farm | Consulta de referências sobre milho ---")
    print("Digite 'sair' para encerrar.")

    while True:
        try:
            user_input = input("\nUser: ")
        except EOFError:
            break

        if user_input.casefold() in {"exit", "quit", "sair"}:
            break

        response = orch.handle_request(user_input, session_state)
        print(f"IA_Farm: {response}")


if __name__ == "__main__":
    main()
