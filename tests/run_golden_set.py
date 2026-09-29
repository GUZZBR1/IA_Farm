"""Run the safety/retrieval Golden Set without external models or APIs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.orchastrator import Orchestrator


class FixtureVectorDB:
    def __init__(self, retrieval: str):
        self.retrieval = retrieval

    def query(self, query: str, k: int = 5, filters: dict[str, Any] | None = None):
        if self.retrieval == "available":
            return [{"text": "validated local context"}]
        return []


def evaluate(case: dict[str, Any]) -> tuple[str, str]:
    orchestrator = Orchestrator(
        db=FixtureVectorDB(case["retrieval"]),
    )
    orchestrator._call_llm = lambda prompt: "ANSWER_FROM_VALIDATED_CONTEXT"
    response = orchestrator.handle_request(case["query"], dict(case["session_state"]))
    normalized = response.casefold()

    missing = [fragment for fragment in case["expected_fragments"] if fragment.casefold() not in normalized]
    forbidden = [fragment for fragment in case["forbidden_fragments"] if fragment.casefold() in normalized]
    if missing or forbidden:
        details = []
        if missing:
            details.append(f"missing={missing}")
        if forbidden:
            details.append(f"forbidden={forbidden}")
        return "FAIL", "; ".join(details)
    return "PASS", response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).with_name("golden_set.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional report path; omitted in CI to avoid generated files.",
    )
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        status, details = evaluate(case)
        results.append({"id": case["id"], "status": status, "details": details})
        print(f"{status}: {case['id']} — {details}")

    failed = [result for result in results if result["status"] != "PASS"]
    if args.report:
        args.report.write_text(
            "# Golden Set guardrail report\n\n"
            + "\n".join(
                f"- **{result['status']}** `{result['id']}`: {result['details']}"
                for result in results
            )
            + "\n",
            encoding="utf-8",
        )
    print(f"Golden Set: {len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
