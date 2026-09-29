"""Run ten repeatable user simulation batteries against the real orchestrator."""

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

from simulation_agents import AGENTS
from tools.orchastrator import Orchestrator


class FixtureVectorDB:
    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = documents
        self.calls: list[dict[str, Any]] = []

    def query(self, query: str, k: int = 5, filters=None):
        self.calls.append({"query": query, "filters": filters})
        return copy.deepcopy(self.documents)


class SimulatedAgronomist:
    """Deterministic model adapter; never contacts a live LLM service."""

    def __init__(self, response: str):
        self.response = response
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def run_agent(battery: dict[str, Any], agent) -> dict[str, Any]:
    database = FixtureVectorDB(battery["documents"])
    simulated_agronomist = SimulatedAgronomist(battery["model_response"])
    app = Orchestrator(db=database)
    app._call_llm = simulated_agronomist
    state = copy.deepcopy(battery["session_state"])
    turns = battery.get("turns", [battery.get("query", "")])
    responses = []
    transcript = []

    for turn in turns:
        user_input = agent.ask(turn)
        retrieval_start = len(database.calls)
        model_start = len(simulated_agronomist.prompts)
        response = app.handle_request(user_input, state)
        responses.append(response)
        transcript.append({
            "user": user_input,
            "assistant": response,
            "session_state": copy.deepcopy(state),
            "retrieval": database.calls[retrieval_start:],
            "model_called": len(simulated_agronomist.prompts) > model_start,
        })

    response = responses[-1]
    combined_prompts = "\n".join(simulated_agronomist.prompts)
    errors = []

    for fragment in battery["expected_fragments"]:
        if fragment.casefold() not in response.casefold():
            errors.append(f"expected response fragment missing: {fragment}")
    for fragment in battery["forbidden_fragments"]:
        if fragment.casefold() in response.casefold():
            errors.append(f"forbidden response fragment present: {fragment}")

    expected_retrieval = battery["expected_retrieval_calls"]
    if len(database.calls) != expected_retrieval:
        errors.append(f"retrieval calls {len(database.calls)} != {expected_retrieval}")

    expected_model = battery["expected_model_calls"]
    if len(simulated_agronomist.prompts) != expected_model:
        errors.append(f"model calls {len(simulated_agronomist.prompts)} != {expected_model}")

    expected_filters = battery.get("expected_filters")
    if expected_filters and (not database.calls or database.calls[-1]["filters"] != expected_filters):
        errors.append(f"last filters {database.calls[-1]['filters'] if database.calls else None} != {expected_filters}")

    expected_last_filters = battery.get("expected_last_filters")
    if expected_last_filters and (not database.calls or database.calls[-1]["filters"] != expected_last_filters):
        errors.append(f"last filters {database.calls[-1]['filters'] if database.calls else None} != {expected_last_filters}")

    for fragment in battery.get("prompt_fragments", []):
        if fragment.casefold() not in combined_prompts.casefold():
            errors.append(f"retrieved prompt fragment missing: {fragment}")

    return {
        "persona": agent.name,
        "passed": not errors,
        "errors": errors,
        "response": response,
        "turn_count": len(turns),
        "transcript": transcript,
    }


def load_batteries(path: Path) -> list[dict[str, Any]]:
    content = json.loads(path.read_text(encoding="utf-8"))
    batteries = content["batteries"]
    if len(batteries) != 10:
        raise ValueError(f"Expected exactly 10 batteries, found {len(batteries)}")
    return batteries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, help="Run one batch, numbered 1 through 10")
    parser.add_argument("--report", type=Path, help="Optional JSON report output")
    parser.add_argument(
        "--cases", type=Path, default=Path(__file__).with_name("golden_set.json")
    )
    args = parser.parse_args()

    batteries = load_batteries(args.cases)
    if args.batch is not None:
        if not 1 <= args.batch <= len(batteries):
            parser.error("--batch must be between 1 and 10")
        batteries = [batteries[args.batch - 1]]

    report = {
        "run": {
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "model": "deterministic test double; no live LLM calls",
            "retriever": "fixture database; no FAISS or network calls",
        },
        "batteries": [],
    }
    total_passed = 0
    total_cases = 0
    for batch_number, battery in enumerate(batteries, start=1 if args.batch is None else args.batch):
        results = [run_agent(battery, agent) for agent in AGENTS]
        passed = sum(result["passed"] for result in results)
        total_passed += passed
        total_cases += len(results)
        status = "PASS" if passed == len(results) else "FAIL"
        print(f"\nBATCH {batch_number:02d}/10 [{status}] {battery['id']}")
        print(f"Goal: {battery['goal']}")
        for result in results:
            mark = "PASS" if result["passed"] else "FAIL"
            print(f"  {mark} {result['persona']} ({result['turn_count']} turn(s))")
            if result["passed"]:
                print(f"    Response: {result['response']}")
            else:
                print(f"    Observed response: {result['response']}")
                for error in result["errors"]:
                    print(f"    Finding: {error}")
        report["batteries"].append({
            "batch": battery["id"],
            "goal": battery["goal"],
            "passed": passed,
            "total": len(results),
            "results": results,
        })
        print(f"  Batch review: {passed}/{len(results)} persona runs passed")
        print(f"  Cumulative: {total_passed}/{total_cases} persona runs passed")
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    print(f"\nSIMULATION RESULT: {total_passed}/{total_cases} persona runs passed")
    return 0 if total_passed == total_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
