# Baseline report

**Snapshot:** 2026-10-01
**Official baseline:** `264a66aba1e1d1857b154314caf36f3559f113f7` (`main`, `origin/main`)
**Scope:** repository, dependency environment, tests, security scan, registry, and local ignored vector-index metadata.

## Repository state

- `main` and `origin/main` pointed to the same commit at inspection time.
- The tracked and non-ignored worktree was clean before validation began.
- The only other known remote branch was `origin/codex/ia-farm-next-stages` at `c875b28`, six commits behind `main` and not ahead of it.
- The current ignored local index is not part of the GitHub baseline. `data/vector_index/` is excluded by `.gitignore`.
- The repository contains a curation registry, but its schema-v1 `entries` array is empty. The agronomic gold set has zero cases; the candidate catalog contains 18 cases and 12 source references.

## Runtime and architecture evidence

- `main.py` is the interactive CLI. It constructs `tools.orchastrator.Orchestrator` and keeps the current region/climate state in a process-local dictionary.
- The response path is deterministic. There is no generative LLM call in the runtime path.
- `tools.vector_db.LocalVectorDB` is the local Sentence-Transformers/FAISS retriever. The optional embedding model is `all-MiniLM-L6-v2`.
- `tools.dosage_calculator` performs arithmetic on a supplied dose; the orchestrator does not invoke it to choose or calculate a recommendation.
- `MemoryManager` persists to SQLite through a compatibility wrapper; the CLI does not load that database into request context.
- A code-level dependency inversion was found: runtime curation validation imported its comparison function from `tests/`. Phase 2 moves the shared validator into `tools/` while retaining the old test-script entry point.

## Local index inspection

The ignored `data/vector_index/` currently contains `faiss.index` (13,869 bytes) and `metadata.json` (5,461 bytes). The metadata file has 9 records from the legacy maize dataset; the report in `PROJECT_STATUS.md` records a prior 9-vector, 384-dimension validation. All 9 current records lack review status, crop, and curation record ID. With an empty registry, **0/9 records are eligible for runtime display**.

The current WSL Python 3.12.3 environment and project `.venv` do not have NumPy, FAISS, or Sentence-Transformers installed. `python3 -m tools.test_libs` reports FAISS and Sentence-Transformers missing; importing the stack stops at missing NumPy. Therefore the real-FAISS validator was **not run** in this baseline. The earlier WSL validation documented in `tests/validation_report.md` is retained as historical evidence, not re-verified here.

## Verification run

Executed on WSL Python 3.12.3; the CI workflow also targets Python 3.11.

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` | **PASS — 58 tests** |
| `python3 tests/run_golden_set.py --report /tmp/ia-farm-baseline-simulation.json` | **PASS — 165 batteries, 660/660 persona runs** |
| `python3 -m tools.security_scan` | **PASS** for its tracked-current-tree patterns |
| `python3 -m compileall -q main.py main_orchestrator.py tools tests` | **PASS** |
| `python3 -m tools.curation_registry` | **PASS — registry valid, 0 approved entries** |
| `python3 -m tools.test_libs` | **FAISS and Sentence-Transformers missing** |
| `tests/validate_real_vector_db.py` | **NOT RUN**; runtime dependencies unavailable |

The 660/660 result verifies only deterministic behavioral contracts against synthetic fixtures and scripted personas. The simulation constructs registry entries with `review_artifacts_verified=True`, so it bypasses review-artifact loading and verification. Its `FixtureVectorDB` ignores query text and `k`, returning all fixtures that match scope. Therefore this result does not validate FAISS, retrieval relevance/ranking, candidate-pool limits, agronomic accuracy, source approval, field behavior, or Android performance.

## Security and reproducibility

- The current-tree scanner found no matching active credential pattern. Its scope is tracked text and a narrow pattern set; it does not establish history cleanup or provider revocation.
- Reachable Git history contains historical credential-shaped values in `tests/final_absolute_run.py` and `tools/orchastrator.py`. Values are intentionally not reproduced here. They were removed from current source in `5f7c8b7`; repository evidence cannot prove provider rotation.
- `requirements.txt` uses version ranges, not a lockfile. The optional model is resolved by name and is not packaged in the repository.
- CI runs dependency-free unit tests, behavioral simulation, the current-tree scanner, and compilation. It does not install the production retrieval dependencies, run the real-vector validator, or execute the constrained CLI smoke.
- Android packaging, offline startup on a clean device, physical performance, agronomic precision, and field use remain unvalidated.

## Baseline decision

Preserve the deterministic response contract, fail-closed curation gate, contextual filtering, isolated arithmetic helper, and distinction between behavioral simulations and agronomic evidence. Phase 2 is limited to documenting the actual and target layers, formalizing the retriever seam, and removing the runtime import from `tests/`. No knowledge is promoted and no agronomic recommendation is added.
