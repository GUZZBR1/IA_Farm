"""Score app runs against a gold set with two independent AI evidence reviews."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


REVIEWER_ROLES = {"maize_evidence_specialist", "independent_verifier"}
OFFICIAL_DOMAINS = (
    "gov.br", "embrapa.br", "inmet.gov.br", "ibge.gov.br",
    "ana.gov.br", "inpe.br", "conab.gov.br",
)


def _is_official_source_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        return (
            parsed.scheme == "https"
            and (host in OFFICIAL_DOMAINS or any(host.endswith("." + domain) for domain in OFFICIAL_DOMAINS))
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def _binomial_tail_probability(trials: int, successes: int, probability: float) -> float:
    """P(X >= successes) for X ~ Binomial(trials, probability)."""

    if successes <= 0:
        return 1.0
    if probability <= 0:
        return 0.0
    if probability >= 1:
        return 1.0

    log_pmf = (
        math.lgamma(trials + 1)
        - math.lgamma(successes + 1)
        - math.lgamma(trials - successes + 1)
        + successes * math.log(probability)
        + (trials - successes) * math.log1p(-probability)
    )
    pmf = math.exp(log_pmf)
    tail = pmf
    for outcome in range(successes, trials):
        pmf *= ((trials - outcome) / (outcome + 1)) * (probability / (1 - probability))
        tail += pmf
    return min(tail, 1.0)


def _precision_lower_confidence_bound(successes: int, trials: int, confidence: float = 0.95) -> float:
    """One-sided exact Clopper-Pearson lower bound for answer precision."""

    if trials <= 0 or successes <= 0:
        return 0.0
    alpha = 1 - confidence
    low, high = 0.0, 1.0
    for _ in range(64):
        midpoint = (low + high) / 2
        if _binomial_tail_probability(trials, successes, midpoint) < alpha:
            low = midpoint
        else:
            high = midpoint
    return low


def validate_gold_set(gold: dict[str, Any]) -> str | None:
    """Return why a gold set is not yet fit for scoring or real app execution."""

    cases = gold.get("cases")
    if not isinstance(cases, list) or not cases:
        return "gold set has no approved cases"

    minimum_coverage = gold.get("minimum_answer_coverage")
    minimum_precision = gold.get("minimum_answer_precision", 0.95)
    if minimum_coverage is None:
        return "minimum_answer_coverage must be agreed before scoring"
    for label, value in (
        ("minimum_answer_coverage", minimum_coverage),
        ("minimum_answer_precision", minimum_precision),
    ):
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError(f"{label} must be a number between 0 and 1")

    case_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(case_ids) != len(cases) or None in case_ids or len(set(case_ids)) != len(cases):
        raise ValueError("gold case IDs must be present and unique")
    independence_groups = [case.get("independence_group") for case in cases]
    if any(not isinstance(group, str) or not group.strip() for group in independence_groups):
        return "each gold case requires a reviewer-assigned independence_group"
    if len(set(independence_groups)) != len(independence_groups):
        return "gold cases must use distinct independence_group values; related variants do not count as independent samples"

    sources = gold.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("gold sources must be an array")
    source_by_id = {source.get("id"): source for source in sources if isinstance(source, dict)}
    if len(source_by_id) != len(sources) or None in source_by_id:
        raise ValueError("gold source IDs must be present and unique")
    for case in cases:
        if case.get("approval_status") != "approved":
            return f"case {case.get('id', '<unknown>')} lacks two independent AI evidence reviews"
        question = case.get("question")
        if not isinstance(question, str) or not question.strip():
            return f"case {case.get('id', '<unknown>')} has no question"
        if not isinstance(case.get("answerable"), bool):
            return f"case {case.get('id', '<unknown>')} must declare answerable as a boolean"
        if not isinstance(case.get("expected_claims"), list):
            return f"case {case.get('id', '<unknown>')} must list expected_claims"
        if any(not isinstance(claim, str) or not claim.strip() for claim in case["expected_claims"]):
            return f"case {case.get('id', '<unknown>')} has malformed expected_claims"
        if case["answerable"] and not case["expected_claims"]:
            return f"answerable case {case.get('id', '<unknown>')} needs expected claims"
        context = case.get("context")
        if not isinstance(context, dict) or not all(
            str(context.get(key, "")).strip() for key in ("crop", "region", "climate")
        ):
            return f"case {case.get('id', '<unknown>')} requires crop, region and climate context"
        if str(context.get("crop", "")).strip().casefold() not in {"maize", "corn", "milho"}:
            return f"case {case.get('id', '<unknown>')} is outside the maize scope"
        record = case.get("review_record", {})
        if not isinstance(record, dict):
            return f"case {case.get('id', '<unknown>')} has malformed AI review metadata"
        reviewer_roles = record.get("reviewer_roles")
        if not isinstance(reviewer_roles, list) or set(reviewer_roles) != REVIEWER_ROLES:
            return f"case {case.get('id', '<unknown>')} requires both independent AI reviewer roles"
        artifacts = record.get("review_artifacts")
        if not isinstance(artifacts, list) or len(artifacts) != 2 or not all(
            isinstance(path, str) and path.strip() for path in artifacts
        ) or len(set(artifacts)) != 2:
            return f"case {case.get('id', '<unknown>')} requires two distinct review artifact paths"
        if not isinstance(record.get("run_report_sha256"), str) or not re.fullmatch(
            r"[0-9a-fA-F]{64}", record["run_report_sha256"]
        ):
            return f"case {case.get('id', '<unknown>')} requires the shared frozen-report SHA-256"
        if record.get("human_agronomist_reviewed") is not False:
            return f"case {case.get('id', '<unknown>')} must record that no human agronomist validation occurred"
        try:
            reviewed_at = date.fromisoformat(str(record.get("reviewed_at", "")))
        except ValueError:
            return f"case {case.get('id', '<unknown>')} has no valid review date"
        if reviewed_at > date.today():
            return f"case {case.get('id', '<unknown>')} has a future review date"
        source_ids = case.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            return f"case {case.get('id', '<unknown>')} has no cited source IDs"
        for source_id in source_ids:
            source = source_by_id.get(source_id)
            if (
                not source
                or not _is_official_source_url(source.get("url"))
                or not source.get("publisher")
                or not source.get("title")
                or not source.get("retrieved_at")
                or source.get("primary_source") is not True
            ):
                return f"case {case.get('id', '<unknown>')} cites an unregistered source"
            try:
                retrieved_at = date.fromisoformat(str(source["retrieved_at"]))
            except ValueError:
                return f"source {source_id} has no valid retrieval date"
            if retrieved_at > date.today():
                return f"source {source_id} has a future retrieval date"

        claim_evidence = case.get("claim_evidence")
        if not isinstance(claim_evidence, list):
            return f"case {case.get('id', '<unknown>')} requires claim_evidence"
        claims = set(case["expected_claims"])
        covered_claims = set()
        for item in claim_evidence:
            if not isinstance(item, dict):
                return f"case {case.get('id', '<unknown>')} has malformed claim evidence"
            claim = item.get("claim")
            if (
                claim not in claims
                or item.get("source_id") not in source_ids
                or not str(item.get("locator", "")).strip()
                or not str(item.get("evidence", "")).strip()
                or item.get("relation") != "supports"
            ):
                return f"case {case.get('id', '<unknown>')} has incomplete claim evidence"
            covered_claims.add(claim)
        if case["answerable"] and covered_claims != claims:
            return f"case {case.get('id', '<unknown>')} lacks source evidence for every expected claim"

    return None


def evaluate(gold: dict[str, Any], reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute answer precision/coverage without using an LLM judge."""

    reason = validate_gold_set(gold)
    if reason:
        return {"status": "not_evaluable", "reason": reason}

    cases = gold["cases"]
    independence_groups = [case["independence_group"] for case in cases]

    minimum_coverage = gold.get("minimum_answer_coverage")
    minimum_precision = gold.get("minimum_answer_precision", 0.95)

    case_by_id = {case.get("id"): case for case in cases}
    if None in case_by_id or len(case_by_id) != len(cases):
        raise ValueError("gold case IDs must be present and unique")
    review_by_id = {review.get("case_id"): review for review in reviews}
    if None in review_by_id or len(review_by_id) != len(reviews):
        raise ValueError("review case IDs must be present and unique")
    if set(review_by_id) != set(case_by_id):
        raise ValueError("reviews must contain exactly one judgment for every gold case")

    substantive = correct_answers = critical_errors = 0
    answerable = answered_answerable = 0
    abstain_expected = correct_abstentions = 0
    for case_id, case in case_by_id.items():
        if not isinstance(case.get("answerable"), bool):
            raise ValueError(f"gold case {case_id} must declare answerable as a boolean")
        review = review_by_id[case_id]
        response_type = review.get("response_type")
        if response_type not in {"answer", "abstain"}:
            raise ValueError(f"review {case_id} response_type must be answer or abstain")

        if case["answerable"]:
            answerable += 1
        else:
            abstain_expected += 1

        if response_type == "answer":
            substantive += 1
            if case["answerable"]:
                answered_answerable += 1
            checks = ("factually_correct", "source_supported", "scope_correct", "critical_error")
            if any(not isinstance(review.get(key), bool) for key in checks):
                raise ValueError(f"answer review {case_id} requires boolean judgments: {checks}")
            critical_errors += int(review["critical_error"])
            is_correct = (
                case["answerable"]
                and review["factually_correct"]
                and review["source_supported"]
                and review["scope_correct"]
                and not review["critical_error"]
            )
            correct_answers += int(is_correct)
        else:
            if not isinstance(review.get("abstention_correct"), bool):
                raise ValueError(f"abstention review {case_id} requires abstention_correct")
            if not case["answerable"]:
                correct_abstentions += int(review["abstention_correct"])

    precision = correct_answers / substantive if substantive else None
    precision_lower_bound = (
        _precision_lower_confidence_bound(correct_answers, substantive)
        if substantive else None
    )
    coverage = answered_answerable / answerable if answerable else None
    abstention_accuracy = (
        correct_abstentions / abstain_expected if abstain_expected else None
    )
    evaluable = precision is not None and coverage is not None
    passed = (
        evaluable
        and precision >= minimum_precision
        and precision_lower_bound >= minimum_precision
        and coverage >= minimum_coverage
        and critical_errors == 0
        and (abstention_accuracy is None or abstention_accuracy == 1)
    )
    return {
        "status": "passed" if passed else "failed" if evaluable else "not_evaluable",
        "cases": len(cases),
        "independent_case_families": len(set(independence_groups)),
        "substantive_answers": substantive,
        "answer_precision": precision,
        "answer_precision_lower_95_ci": precision_lower_bound,
        "answer_coverage": coverage,
        "correct_abstention_rate": abstention_accuracy,
        "critical_errors": critical_errors,
        "thresholds": {
            "minimum_answer_precision": minimum_precision,
            "confidence": 0.95,
            "precision_test": "one-sided exact Clopper-Pearson lower bound",
            "minimum_answer_coverage": minimum_coverage,
            "maximum_critical_errors": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold", type=Path, help="Gold case set with two independent AI evidence reviews")
    parser.add_argument("reviews", type=Path, help="Judgments for the frozen application run")
    args = parser.parse_args()

    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    reason = validate_gold_set(gold)
    if reason:
        print(json.dumps({"status": "not_evaluable", "reason": reason}, ensure_ascii=False, indent=2))
        return 2
    if not args.reviews.is_file():
        print(json.dumps({
            "status": "not_evaluable",
            "reason": f"review results file does not exist: {args.reviews}",
        }, ensure_ascii=False, indent=2))
        return 2
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    result = evaluate(gold, reviews)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
