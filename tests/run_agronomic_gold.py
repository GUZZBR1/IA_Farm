"""Run the AI evidence-reviewed agronomic gold set through the local RAG path."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agronomic_benchmark import validate_gold_set
from tools.orchastrator import Orchestrator


def run_cases(orchestrator: Orchestrator, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Capture app output for independent AI review without exposing expected claims."""

    outputs = []
    for case in cases:
        session_state = dict(case["context"])
        response = orchestrator.handle_request(case["question"], session_state)
        outputs.append({
            "case_id": case["id"],
            "question": case["question"],
            "context": case["context"],
            "response": response,
            "final_session_state": session_state,
        })
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gold",
        type=Path,
        default=PROJECT_ROOT / "tests" / "agronomic_gold_set.json",
        help="Gold set with two independent AI evidence reviews (drafts are rejected)",
    )
    parser.add_argument("--output", type=Path, help="Optional path for reviewer transcripts")
    args = parser.parse_args()

    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    reason = validate_gold_set(gold)
    if reason:
        print(f"NOT RUN: {reason}", file=sys.stderr)
        return 2

    try:
        orchestrator = Orchestrator()
    except Exception as exc:
        print(
            "Could not initialize the application's local retrieval path. "
            f"Check requirements and the approved local index: {exc}",
            file=sys.stderr,
        )
        return 2

    result = {
        "run": {
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
            ).strip(),
            "response_engine": "application deterministic RAG; no generative model",
            "review_instructions": (
                "Review each response against the separately held approved gold set; "
                "do not infer correctness from successful execution."
            ),
        },
        "outputs": run_cases(orchestrator, gold["cases"]),
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote independent-review transcripts to {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
