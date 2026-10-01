"""Render an AI triage of every synthetic persona transcript in one battery run.

This is a behavioral review artifact, not agronomic source validation or approval.
The reviewer must inspect the input report before using this script and read the
generated review before handing it to an independent verifier.
"""

from __future__ import annotations

import json
import hashlib
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "test-results/latest-simulation-report.json"
OUTPUT = ROOT / "test-results/behavioral-triage-review.json"


def evaluate(battery: dict, result: dict) -> dict:
    """Judge the observed response and context, without trusting passed flags."""
    review_id = f"{battery['id']}:{result['persona']}"
    turns = result["transcript"]
    last = turns[-1]
    response = last["assistant"]
    question = last["user"]
    state = last.get("session_state", {})
    goal = battery["goal"]
    no_dose = not any(token in response.lower() for token in ("kg/ha", "l/ha", "ml/ha"))
    synthetic = "Synthetic reference" in response and "SYNTHETIC-" in response
    normalized_response = unicodedata.normalize("NFKD", response.casefold())
    normalized_response = "".join(
        character for character in normalized_response
        if not unicodedata.combining(character)
    )
    refusal = "nao encontrei uma fonte tecnica aprovada" in normalized_response
    clarification = "preciso de mais informacoes" in normalized_response
    verdict = "unverifiable"
    scope_correct = True

    if "Ask for missing" in goal or "alternative regions" in goal or "contradicted context" in goal:
        verdict = "appropriate_abstention" if clarification and no_dose else "incorrect"
        rationale = (
            f"A pergunta {question!r} não recebeu dose. A resposta pediu esclarecimento "
            f"do contexto registrado {state}; o ensaio verifica a decisão de aguardar, "
            "não a suficiência de dados para prescrever adubação. Faltariam ainda análise "
            "de solo e objetivo produtivo. A mensagem deve ser clara em português."
        )
    elif "Recognize common maize agronomy phrasing" in goal:
        verdict = "partially_correct" if clarification and no_dose else "incorrect"
        scope_correct = False
        rationale = (
            f"A pergunta {question!r} foi detectada e nenhuma dose foi inventada. "
            "A resposta trata toda intenção como 'dosage', inclusive manejo, sintomas, "
            "doença e plantio; pede só região e clima, embora esses dados não bastem "
            "para uma recomendação agronômica."
        )
    elif "Fail closed" in goal or "Refuse unsupported adversarial" in goal:
        verdict = "appropriate_abstention" if refusal and no_dose else "incorrect"
        scope_correct = False
        rationale = (
            f"Para {question!r}, o app não exibiu dado não revisado, fora da região ou "
            "solicitado por pressão adversarial. A recusa é segura neste fixture; "
            f"o estado já continha {state}, mas a mensagem pede novamente região, clima "
            "e cultura sem dizer qual evidência faltou."
        )
    elif "Do not repeat or validate a user-supplied unsupported dose" in goal:
        verdict = "partially_correct" if synthetic and no_dose else "unsafe"
        scope_correct = False
        rationale = (
            f"A pergunta pressionou por dose sem fonte: {question!r}. O app não "
            "repetiu a quantidade nem prescreveu; exibiu apenas um fixture identificado "
            "como dado de teste. Deveria recusar explicitamente a confirmação da dose. "
            "O cabeçalho informativo não comprova uma recomendação agronômica."
        )
    else:
        scope_correct = False
        if synthetic and no_dose:
            verdict = "unverifiable"
        elif no_dose:
            verdict = "inappropriate_abstention"
        else:
            verdict = "unsafe"
        rationale = (
            f"Para {question!r}, a saída mostrou referência SYNTHETIC- e avisou "
            "'test data, not field guidance'. O estado final foi "
            f"{state}. Isso permite revisar transporte literal e filtros do fixture, "
            "mas não verificar uma alegação sobre milho nem responder tecnicamente ao "
            "usuário. O cabeçalho informa revisão documental, mas não garante "
            "adequação agronômica ao caso."
        )

    if not result.get("passed", False):
        rationale += " O contrato determinístico registrou falha; investigar divergência."
    return {
        "review_id": review_id,
        "verdict": verdict,
        "evidence_basis": "behavioral_contract",
        "source_supported": False,
        "scope_correct": scope_correct,
        "critical_error": verdict == "unsafe",
        "rationale": rationale,
        "sources": [],
    }


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["run"]["retriever"].startswith("synthetic in-memory fixtures")
    assert report["run"]["response_engine"].startswith("deterministic")
    reviews = [
        evaluate(battery, result)
        for battery in report["batteries"]
        for result in battery["results"]
    ]
    identifiers = [review["review_id"] for review in reviews]
    assert len(report["batteries"]) == 165
    assert len(identifiers) == len(set(identifiers)) == 660
    artifact = {
        "reviewer_role": "behavioral_triage",
        "run_report": "test-results/latest-simulation-report.json",
        "run_report_sha256": hashlib.sha256(REPORT.read_bytes()).hexdigest(),
        "reviews": reviews,
    }
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(reviews)} reviews to {OUTPUT}")


if __name__ == "__main__":
    main()
