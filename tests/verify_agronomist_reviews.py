"""Compare independent source-based reviews without treating agreement as truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from datetime import date
from typing import Any
from urllib.parse import urlsplit


VERDICTS = {
    "correct",
    "partially_correct",
    "incorrect",
    "unsupported",
    "unsafe",
    "appropriate_abstention",
    "inappropriate_abstention",
    "unverifiable",
}
OFFICIAL_DOMAINS = (
    "gov.br",
    "embrapa.br",
    "inmet.gov.br",
    "ibge.gov.br",
    "ana.gov.br",
    "inpe.br",
    "conab.gov.br",
)
JUDGMENT_FIELDS = (
    "verdict",
    "evidence_basis",
    "source_supported",
    "scope_correct",
    "critical_error",
)
SOURCE_FIELDS = (
    "title",
    "publisher",
    "source_type",
    "edition_or_validity",
    "accessed_at",
    "locator",
    "evidence",
    "claim_ids",
)


def _is_official_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        return (
            parsed.scheme == "https"
            and bool(host)
            and (host in OFFICIAL_DOMAINS or any(host.endswith("." + domain) for domain in OFFICIAL_DOMAINS))
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def _index_reviews(report: dict[str, Any], expected_role: str) -> dict[str, dict[str, Any]]:
    if report.get("reviewer_role") != expected_role:
        raise ValueError(f"reviewer_role must be {expected_role!r}")
    if not isinstance(report.get("run_report"), str) or not report["run_report"].strip():
        raise ValueError("run_report must identify the battery report reviewed")
    if not isinstance(report.get("run_report_sha256"), str) or not re.fullmatch(
        r"[0-9a-fA-F]{64}", report["run_report_sha256"]
    ):
        raise ValueError("run_report_sha256 must contain the SHA-256 of the frozen report")
    reviews = report.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        raise ValueError("reviews must be a non-empty array")

    indexed: dict[str, dict[str, Any]] = {}
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError("each review must be an object")
        review_id = review.get("review_id")
        if not isinstance(review_id, str) or not review_id.strip():
            raise ValueError("each review requires a non-empty review_id")
        if review_id in indexed:
            raise ValueError(f"duplicate review_id: {review_id}")
        if review.get("verdict") not in VERDICTS:
            raise ValueError(f"review {review_id} has an invalid verdict")
        for field in ("source_supported", "scope_correct", "critical_error"):
            if not isinstance(review.get(field), bool):
                raise ValueError(f"review {review_id} requires boolean {field}")
        if not isinstance(review.get("rationale"), str) or not review["rationale"].strip():
            raise ValueError(f"review {review_id} requires a rationale")
        sources = review.get("sources")
        evidence_basis = review.get("evidence_basis")
        if evidence_basis not in {"primary_source", "behavioral_contract", "unavailable"}:
            raise ValueError(f"review {review_id} requires a valid evidence_basis")
        if not isinstance(sources, list):
            raise ValueError(f"review {review_id} sources must be an array")
        if evidence_basis == "primary_source" and not sources:
            raise ValueError(f"review {review_id} requires primary-source evidence")
        if evidence_basis != "primary_source" and sources:
            raise ValueError(
                f"review {review_id} may cite sources only with evidence_basis='primary_source'"
            )
        for source in sources:
            if not isinstance(source, dict) or not _is_official_https_url(source.get("url")):
                raise ValueError(f"review {review_id} source URL must use an official HTTPS domain")
            for field in SOURCE_FIELDS:
                if field not in source or source[field] in (None, "", []):
                    raise ValueError(f"review {review_id} source requires {field}")
            if any(
                not isinstance(source[field], str) or not source[field].strip()
                for field in SOURCE_FIELDS
                if field != "claim_ids"
            ):
                raise ValueError(f"review {review_id} source metadata fields must be non-empty strings")
            if source["source_type"] not in {
                "official_regulatory",
                "official_research",
                "official_dataset",
            }:
                raise ValueError(f"review {review_id} source has an invalid source_type")
            try:
                date.fromisoformat(source["accessed_at"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"review {review_id} source accessed_at must be an ISO date") from error
            if not isinstance(source["claim_ids"], list) or not all(
                isinstance(claim_id, str) and claim_id.strip() for claim_id in source["claim_ids"]
            ):
                raise ValueError(f"review {review_id} source claim_ids must be non-empty strings")
        indexed[review_id] = review
    return indexed


def compare_reviews(master: dict[str, Any], verifier: dict[str, Any]) -> dict[str, Any]:
    """Compare judgments; report citation differences without treating them as verdict conflicts."""
    master_reviews = _index_reviews(master, "maize_evidence_specialist")
    verifier_reviews = _index_reviews(verifier, "independent_verifier")
    if master["run_report"] != verifier["run_report"]:
        raise ValueError("master and verifier must cite the same run_report")
    if master["run_report_sha256"].lower() != verifier["run_report_sha256"].lower():
        raise ValueError("master and verifier must cite the same run_report_sha256")
    if master_reviews.keys() != verifier_reviews.keys():
        missing_verifier = sorted(master_reviews.keys() - verifier_reviews.keys())
        missing_master = sorted(verifier_reviews.keys() - master_reviews.keys())
        raise ValueError(
            "review_id coverage differs; "
            f"missing_verifier={missing_verifier}, missing_master={missing_master}"
        )

    disagreements = []
    source_variations = []
    for review_id in sorted(master_reviews):
        first, second = master_reviews[review_id], verifier_reviews[review_id]
        differences = {
            field: {"master": first[field], "verifier": second[field]}
            for field in JUDGMENT_FIELDS
            if first[field] != second[field]
        }
        if differences:
            disagreements.append({"review_id": review_id, "differences": differences})
        if first["sources"] != second["sources"]:
            source_variations.append({
                "review_id": review_id,
                "master_sources": first["sources"],
                "verifier_sources": second["sources"],
            })

    all_behavioral = all(
        master_reviews[review_id]["evidence_basis"] == "behavioral_contract"
        and verifier_reviews[review_id]["evidence_basis"] == "behavioral_contract"
        for review_id in master_reviews
    )
    all_source_supported = all(
        all(
            report[review_id]["evidence_basis"] == "primary_source"
            and report[review_id]["source_supported"]
            and report[review_id]["scope_correct"]
            and not report[review_id]["critical_error"]
            and report[review_id]["verdict"] in {"correct", "appropriate_abstention"}
            for report in (master_reviews, verifier_reviews)
        )
        for review_id in master_reviews
    )
    if disagreements:
        status = "contested_or_insufficient_evidence"
    elif all_behavioral:
        status = "behavioral_only"
    elif all_source_supported:
        status = "agent_agreement_official_sources"
    else:
        status = "contested_or_insufficient_evidence"

    agreements = len(master_reviews) - len(disagreements)
    return {
        "status": status,
        "run_report": master["run_report"],
        "run_report_sha256": master["run_report_sha256"].lower(),
        "reviews_compared": len(master_reviews),
        "agreements": agreements,
        "disagreements": disagreements,
        "source_variations": source_variations,
        "human_approval_required": False,
        "professional_certification_claim_permitted": False,
        "precision_claim_permitted": False,
        "note": (
            "Concordância de julgamento significa apenas que os agentes deram as mesmas "
            "classificações. Citações independentes podem variar e são listadas separadamente; "
            "o comparador valida domínios, estrutura e consistência, mas não autentica documentos "
            "nem prova precisão agronômica global. Casos parcialmente corretos ou com divergência "
            "continuam bloqueados."
        ),
    }


def verify_report_file(report: dict[str, Any], base_dir: Path) -> None:
    """When run from the CLI, ensure the frozen report matches its declared hash."""
    path = Path(report["run_report"])
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        raise ValueError(f"run_report does not exist: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual.lower() != report["run_report_sha256"].lower():
        raise ValueError("run_report_sha256 does not match the report file contents")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("master", type=Path, help="Agronomist Master JSON review")
    parser.add_argument("verifier", type=Path, help="Independent verifier JSON review")
    parser.add_argument("--output", type=Path, help="Optional path to save the comparison report")
    args = parser.parse_args()
    master = json.loads(args.master.read_text(encoding="utf-8"))
    verifier = json.loads(args.verifier.read_text(encoding="utf-8"))
    result = compare_reviews(master, verifier)
    verify_report_file(master, Path.cwd())
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "reviews_compared": result["reviews_compared"],
        "agreements": result["agreements"],
        "disagreements": len(result["disagreements"]),
        "source_variations": len(result["source_variations"]),
        "report": str(args.output) if args.output else None,
    }, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"behavioral_only", "agent_agreement_official_sources"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
