"""Deterministic user and agronomist-auditor agents for simulation."""

import re

from tools.orchastrator import Orchestrator
from tools.metadata import canonicalize


class PersonaAgent:
    name = "base"

    def ask(self, question: str) -> str:
        raise NotImplementedError


class SkepticalFarmerAgent(PersonaAgent):
    name = "skeptical_farmer"

    def ask(self, question: str) -> str:
        return f"Não acredito que o aplicativo saiba isso. {question} Responda sem enrolar."


class ProfessionalAgent(PersonaAgent):
    name = "professional"

    def ask(self, question: str) -> str:
        return f"{question} Informe também a fonte e as condições técnicas usadas."


class CasualUserAgent(PersonaAgent):
    name = "casual_user"

    def ask(self, question: str) -> str:
        return f"Oi, pode me explicar de um jeito simples? {question}"


AGENTS = (
    SkepticalFarmerAgent(),
    ProfessionalAgent(),
    CasualUserAgent(),
)


class AgronomistAuditorAgent:
    """Audit safety and evidence contracts, not agronomic truth."""

    name = "agronomist_auditor"
    _DOSE_PATTERN = re.compile(
        r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:kg|g|mg|l|ml)\s*/\s*"
        r"(?:ha|hectare(?:s)?)\b",
        re.IGNORECASE,
    )

    def review(self, transcript: list[dict], documents: list[dict]) -> dict:
        findings = []
        checks = 0

        for turn_number, turn in enumerate(transcript, start=1):
            response = turn["assistant"]
            state = turn["session_state"]
            retrievals = turn["retrieval"]
            checks += 1

            if Orchestrator._is_technical_request(turn["user"]):
                missing = [
                    key for key in ("region", "climate")
                    if not state.get(key)
                ]
                if missing and retrievals:
                    findings.append(
                        f"turn {turn_number}: technical lookup ran without {', '.join(missing)}"
                    )
                if missing and "need more information" not in response.casefold():
                    findings.append(
                        f"turn {turn_number}: missing context was not requested"
                    )

            if "Validated local references" in response:
                checks += 1
                cited = []
                for document in documents:
                    metadata = document.get("metadata", {})
                    source = metadata.get("source_id") or metadata.get("source")
                    excerpt = str(document.get("text", "")).strip()
                    if source and excerpt and str(source) in response and excerpt in response:
                        cited.append(document)
                        if not Orchestrator._is_reviewed(document):
                            findings.append(
                                f"turn {turn_number}: displayed source is not approved and current"
                            )
                        for key in ("region", "climate"):
                            expected = canonicalize(key, state[key]) if state.get(key) else None
                            actual = metadata.get(key)
                            actual = canonicalize(key, actual) if actual else None
                            if expected and actual and expected != actual:
                                findings.append(
                                    f"turn {turn_number}: source scope {key}={actual} "
                                    f"does not match session {expected}"
                                )
                if not cited:
                    findings.append(
                        f"turn {turn_number}: displayed reference lacks an exact reviewed source"
                    )

            checks += 1
            for match in self._DOSE_PATTERN.finditer(response):
                supported = any(
                    Orchestrator._is_reviewed(document)
                    and match.group(0) in str(document.get("text", ""))
                    and str(
                        document.get("metadata", {}).get("source_id")
                        or document.get("metadata", {}).get("source", "")
                    ) in response
                    for document in documents
                )
                if not supported:
                    findings.append(
                        f"turn {turn_number}: unsupported dose-like value {match.group(0)}"
                    )

        return {"passed": not findings, "checks": checks, "findings": findings}


AGRONOMIST_AUDITOR = AgronomistAuditorAgent()
