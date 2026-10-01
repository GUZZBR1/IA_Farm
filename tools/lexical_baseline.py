"""Auditable BM25 baseline for retrieval mechanics, using only the standard library."""

from __future__ import annotations

from collections import Counter
import math
import re
import unicodedata
from typing import Any

from tools.metadata import metadata_matches


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def record_metadata(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("metadata", record)


def matches_filters(record: dict[str, Any], filters: dict[str, Any]) -> bool:
    metadata = record_metadata(record)
    return all(metadata_matches(key, metadata.get(key), value) for key, value in filters.items())


class LexicalBaseline:
    """BM25 with corpus-wide IDF, pre-ranking metadata filters, and stable ID ties.

    Each input record is one scoring unit. No stemming, synonyms, stop-word removal,
    embeddings, or learned weights are used. Queries with zero overlap return no hits.
    """

    def __init__(self, records: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("k1 must be positive and b must be between zero and one")
        self.records = records
        self.k1, self.b = k1, b
        self.terms = [Counter(tokenize(record["text"])) for record in records]
        self.lengths = [sum(terms.values()) for terms in self.terms]
        self.average_length = sum(self.lengths) / len(records) if records else 0
        self.frequency = Counter(term for terms in self.terms for term in terms)

    def query(self, query: str, k: int = 5, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if k <= 0 or not self.average_length:
            return []
        query_terms = set(tokenize(query))
        ranked = []
        for index, record in enumerate(self.records):
            if not matches_filters(record, filters or {}):
                continue
            score = 0.0
            for term in sorted(query_terms):
                count = self.terms[index][term]
                if not count:
                    continue
                frequency = self.frequency[term]
                idf = math.log(1 + (len(self.records) - frequency + 0.5) / (frequency + 0.5))
                normalization = self.k1 * (1 - self.b + self.b * self.lengths[index] / self.average_length)
                score += idf * count * (self.k1 + 1) / (count + normalization)
            if score > 0:
                ranked.append((score, record_metadata(record)["eval_record_id"], record))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [{**record, "retrieval_score": float(score)} for score, _, record in ranked[:k]]
