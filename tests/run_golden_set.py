"""Run deterministic user-simulation batteries without generated responses."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from battery_catalog import build_batteries
from device_profiles import DEVICE_PROFILES
from simulation_agents import AGENTS, AGRONOMIST_AUDITOR
from tools.orchastrator import Orchestrator


class FixtureVectorDB:
    """In-memory retriever with no embedding model, disk or network dependency."""

    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = documents
        self.calls: list[dict[str, Any]] = []

    def query(self, query: str, k: int = 5, filters=None):
        self.calls.append({"query": query, "filters": copy.deepcopy(filters)})
        matching = []
        for document in self.documents:
            metadata = document.get("metadata", {})
            if all(metadata.get(key) == value for key, value in (filters or {}).items()):
                matching.append(document)
        return copy.deepcopy(matching)


def run_agent(battery: dict[str, Any], agent) -> dict[str, Any]:
    database = FixtureVectorDB(battery["documents"])
    app = Orchestrator(db=database)
    state = copy.deepcopy(battery["session_state"])
    responses = []
    transcript = []

    for turn in battery["turns"]:
        user_input = agent.ask(turn)
        retrieval_start = len(database.calls)
        response = app.handle_request(user_input, state)
        responses.append(response)
        transcript.append({
            "user": user_input,
            "assistant": response,
            "session_state": copy.deepcopy(state),
            "retrieval": database.calls[retrieval_start:],
        })

    response = responses[-1]
    errors = []
    for fragment in battery["expected_fragments"]:
        if fragment.casefold() not in response.casefold():
            errors.append(f"expected response fragment missing: {fragment}")
    for fragment in battery["forbidden_fragments"]:
        if fragment.casefold() in response.casefold():
            errors.append(f"forbidden response fragment present: {fragment}")

    if len(database.calls) != battery["expected_retrieval_calls"]:
        errors.append(
            f"retrieval calls {len(database.calls)} != {battery['expected_retrieval_calls']}"
        )
    expected_filters = battery.get("expected_filters")
    if expected_filters and (
        not database.calls or database.calls[-1]["filters"] != expected_filters
    ):
        actual = database.calls[-1]["filters"] if database.calls else None
        errors.append(f"last filters {actual} != {expected_filters}")
    expected_state = battery.get("expected_state")
    if expected_state and any(state.get(key) != value for key, value in expected_state.items()):
        errors.append(f"session state {state} does not include {expected_state}")

    agronomist_review = AGRONOMIST_AUDITOR.review(transcript, database.documents)
    errors.extend(agronomist_review["findings"])

    return {
        "persona": agent.name,
        "passed": not errors,
        "errors": errors,
        "agronomist_review": agronomist_review,
        "response": response,
        "turn_count": len(battery["turns"]),
        "retrieval_calls": len(database.calls),
        "transcript": transcript,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, help="Run one numbered battery")
    parser.add_argument("--report", type=Path, help="Optional JSON report output")
    parser.add_argument(
        "--device-profile",
        choices=sorted(DEVICE_PROFILES),
        default="android-low-mid-4gb",
        help="Declared device assumptions; does not emulate physical hardware",
    )
    args = parser.parse_args()

    batteries = build_batteries()
    total_batteries = len(batteries)
    if args.batch is not None:
        if not 1 <= args.batch <= len(batteries):
            parser.error(f"--batch must be between 1 and {len(batteries)}")
        batteries = [batteries[args.batch - 1]]

    report = {
        "run": {
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "response_engine": "deterministic; generative model disabled",
            "retriever": "synthetic in-memory fixtures; no embedding model, FAISS or network",
            "safety_note": "all dose-related fixtures are synthetic and non-prescriptive",
            "device_profile": {
                "id": args.device_profile,
                **DEVICE_PROFILES[args.device_profile],
            },
        },
        "batteries": [],
    }
    total_passed = total_cases = 0
    failures = []
    offset = 1 if args.batch is None else args.batch

    print(
        "DEVICE PROFILE: "
        f"{args.device_profile} ({DEVICE_PROFILES[args.device_profile]['total_ram_mb']} MB declared; "
        "behavioral simulation only, no Android hardware emulation)"
    )

    for battery_number, battery in enumerate(batteries, start=offset):
        results = [run_agent(battery, agent) for agent in AGENTS]
        passed = sum(result["passed"] for result in results)
        total_passed += passed
        total_cases += len(results)
        if passed != len(results):
            failures.append(battery["id"])

        report["batteries"].append({
            "number": battery_number,
            "id": battery["id"],
            "goal": battery["goal"],
            "passed": passed,
            "total": len(results),
            "review": "PASS: all persona contracts met" if passed == len(results) else "FAIL: inspect persona findings",
            "results": results,
        })
        print(
            f"BATTERY {battery_number:03d}/{total_batteries} "
            f"[{passed}/{len(results)}] {battery['id']}"
        )
        print(f"  Review: {report['batteries'][-1]['review']}")
        for result in results:
            label = "PASS" if result["passed"] else "FAIL"
            print(f"  {label} {result['persona']} ({result['turn_count']} turns)")
            for error in result["errors"]:
                print(f"    Finding: {error}")

        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    print(f"\nSIMULATION RESULT: {total_passed}/{total_cases} persona runs passed")
    if failures:
        print("Batteries requiring evaluation/fix: " + ", ".join(failures))
    return 0 if total_passed == total_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
