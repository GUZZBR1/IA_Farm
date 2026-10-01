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
from tools.metadata import canonicalize
from tools.curation_registry import CurationRegistry, text_sha256
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
            metadata = document.get("metadata", document)
            if all(
                canonicalize(key, metadata.get(key)) == canonicalize(key, value)
                for key, value in (filters or {}).items()
            ):
                matching.append(document)
        return copy.deepcopy(matching)


def run_agent(battery: dict[str, Any], agent) -> dict[str, Any]:
    documents = copy.deepcopy(battery["documents"])
    entries = {}
    for index, document in enumerate(documents):
        metadata = document.get("metadata", document)
        record_id = f"SIMULATION-{battery['id']}-{index}"
        metadata["curation_record_id"] = record_id
        metadata["approved_scope"] = {
            key: value for key, value in metadata.items()
            if key not in {"curation_record_id", "knowledge_record_id", "knowledge_release_id",
                           "source_id", "source", "knowledge_status", "review_status",
                           "review_date", "reviewed_at", "review_input_sha256",
                               "approved_scope", "valid_from", "valid_until", "text", "retrieval_distance"}
        }
        source = metadata.get("source_id") or metadata.get("source")
        reviewed_at = metadata.get("review_date") or metadata.get("reviewed_at")
        entries[record_id] = {
            "record_id": record_id,
            "approval_status": "approved",
            "text_sha256": text_sha256(str(document.get("text", "")).strip()),
            "source_id": source,
            "crop": metadata.get("crop"),
            "review_date": reviewed_at,
            "review_artifacts_verified": True,
            "source_snapshots_verified": True,
            "human_approval_verified": True,
            "review_input_sha256": "synthetic-fixture-only",
            "approved_scope": metadata["approved_scope"],
        }
    database = FixtureVectorDB(documents)
    app = Orchestrator(db=database, curation_registry=CurationRegistry(entries=entries))
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
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "test-results" / "latest-simulation-report.json",
        help="JSON evidence packet for the Agronomist Master review",
    )
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
        "summary": {
            "status": "running",
            "batteries_completed": 0,
            "persona_runs": 0,
            "persona_runs_passed": 0,
            "behavioral_pass_rate": None,
            "agronomic_precision": None,
            "agronomic_precision_status": "not_measured",
        },
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

        report["summary"].update({
            "batteries_completed": len(report["batteries"]),
            "persona_runs": total_cases,
            "persona_runs_passed": total_passed,
            "behavioral_pass_rate": total_passed / total_cases if total_cases else None,
        })
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"\nSIMULATION RESULT: {total_passed}/{total_cases} persona runs passed")
    if failures:
        print("Batteries requiring evaluation/fix: " + ", ".join(failures))
    report["run"]["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["summary"]["status"] = "completed_with_failures" if failures else "completed"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"REVIEW PACKET: {args.report}")
    return 0 if total_passed == total_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
