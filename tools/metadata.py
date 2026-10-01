"""Canonical metadata values shared by ingestion, the CLI and retrieval."""

import re
import unicodedata
from typing import Any


ALIASES = {
    "region": {
        "mt": "Brazil-MatoGrosso",
        "mato grosso": "Brazil-MatoGrosso",
        "cerrado": "Brazil-MatoGrosso",
        "pr": "Brazil-Parana",
        "parana": "Brazil-Parana",
        "sp": "Brazil-SaoPaulo",
        "sao paulo": "Brazil-SaoPaulo",
        "mg": "Brazil-MinasGerais",
        "minas gerais": "Brazil-MinasGerais",
        "ba": "Brazil-Bahia",
        "bahia": "Brazil-Bahia",
    },
    "climate": {
        "tropical": "Tropical",
        "equatorial": "Tropical",
        "subtropical": "Subtropical",
        "temperate": "Temperate",
        "semi arid": "Semi-arid",
        "semi arido": "Semi-arid",
        "semiarido": "Semi-arid",
        "semi-arid": "Semi-arid",
        "arid": "Arid",
    },
}


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold().strip()
    text = re.sub(r"[-_]+", " ", text)
    return re.sub(r"\s+", " ", text)


def canonicalize(category: str, value: Any) -> str:
    """Return the canonical value used by indexed metadata.

    Unknown values are normalized but preserved so the system can still ask
    for clarification instead of silently treating them as known regions.
    """

    if value is None:
        return ""

    text = str(value).strip()
    aliases = ALIASES.get(category, {})
    alias = aliases.get(_key(text))
    if alias:
        return alias

    for canonical in aliases.values():
        if _key(canonical) == _key(text):
            return canonical

    return text


def metadata_matches(category: str, left: Any, right: Any) -> bool:
    """Compare metadata using the same canonicalization on both sides."""

    return canonicalize(category, left) == canonicalize(category, right)
