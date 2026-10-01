# IA_Farm architecture

**Status:** CURRENT ARCHITECTURE for the implemented system, with target boundaries clearly marked as future work.
**Baseline:** `2c2082f304ba93531cfea2988946f622089f38ef`.

This document describes the real runtime first. The target architecture is a direction for incremental work; it does not imply that a layer is already implemented.

## Current system map

```text
Farmer / operator
        │ text
        ▼
Presentation: main.py (interactive CLI; caller owns session dict)
        │ handle_request(text, session_state) -> str
        ▼
Application orchestration: tools/orchastrator.py
        ├── deterministic intent keywords
        ├── deterministic region/climate extraction and clarification
        ├── retrieval request with available context filters
        ├── eligibility and scope checks
        └── literal source excerpt or fail-closed response
                │
                ├── Retrieval port: VectorRetriever.query(query, filters)
                │       └── LocalVectorDB → Sentence-Transformers → FAISS
                │
                ├── Evidence authorization: CurationRegistry
                │       └── exact excerpt hash + linked review artifacts
                │
                └── Metadata policy: tools/metadata.py

Knowledge preparation: Markdown parser → candidate artifact only (no automatic index publication)
Canonical knowledge store: `data/knowledge_base/approved_records.json` (currently empty)
Release: validated PUBLISHED records → hashed manifest → disposable index builder
Farm memory: SQLite helper, called by compatibility wrapper, not CLI context
Deterministic arithmetic: isolated utility, not selected by the orchestrator
Language generation: absent from application response path
Evaluation: tests/ (fixtures, contract tests, simulation, validation scripts)
```

The current curation registry has zero entries. The local ignored FAISS index has nine legacy chunks but is unversioned and rejected by the current loader. Vector startup requires a compatible index plus an explicitly configured local embedding artifact; this WSL environment lacks the vector packages. The runtime has no approved maize corpus to answer from and remains fail-closed when retrieval capability is unavailable.

## Implemented layer inventory

| Layer | Current implementation | Boundary and limit |
|---|---|---|
| Knowledge Preparation | `tools/ingest.py`, `tools/mining_agent.py`, `tools/knowledge_schema.py`, `tools/knowledge_lifecycle.py`, `tools/knowledge_store.py` | Local Markdown parse outputs candidates only. Lifecycle emits hash-linked audit events and `KnowledgeStore` persists state/events atomically in SQLite; authenticated operators and deployment-level access control remain caller responsibilities. |
| Knowledge Base | `data/knowledge_base/approved_records.json`, `data/curation_registry.json` | Canonical starter store is empty. Registry is the runtime display authorization source and is empty. FAISS vectors are disposable derived files. |
| Retrieval | `tools/vector_db.py`, `tools/contracts.py`, `tools/lexical_baseline.py`, `tools/retrieval_evaluation.py`, `tools/retrieval_runtime.py` | Runtime vector path requires a pinned local model and a compatible versioned FAISS index; current environment cannot start that path. BM25 is an offline baseline and never an implicit fallback. No agronomic threshold or semantic comparison is validated without approved labeled records. |
| Context | Helpers inside `tools/orchastrator.py`; aliases in that module and `tools/metadata.py` | Current required fields for recognized technical questions are region and climate. There is no standalone Context Engine or per-intent schema yet. |
| Safety / evidence authorization | `Orchestrator.rag_query`, `_is_reviewed`, `_matches_context`, `CurationRegistry` | Requires eligible crop/source/review metadata, registry binding and compatible scope. This is deterministic but not a complete formal state machine. |
| Application Orchestrator | `tools/orchastrator.py` | Coordinates request parsing, context checks, retrieval, authorization, and string response. Does not invoke memory or dosage arithmetic. |
| Farm Memory | `tools/memory_manager.py` | SQLite profile/history helper; only the compatibility wrapper writes history. No expiry, consent, provenance-state model, or automatic context read. |
| Deterministic Tools | `tools/dosage_calculator.py`, `tools/calculator.py` | Arithmetic only on a supplied per-hectare dose. Not a dose-selection engine and not connected to the current request path. |
| Language Layer | None in runtime | Embeddings represent queries for search; no generative answer or SLM. Vision extraction is a separate remote preparation experiment. |
| Interface | `main.py` | Terminal UI only; no Android, web, voice, or camera implementation. |
| Evaluation | `tests/` | Unit/contract tests and synthetic behavior simulation are separate from agronomic truth validation. The simulation bypasses review-artifact verification by injecting pre-verified registry entries; its `FixtureVectorDB` ignores query text and `k`, so it does not measure FAISS relevance, ranking, or candidate-pool behavior. |

## Current contracts

### Retriever port

`VectorRetriever` is a structural protocol. A runtime retriever accepts the query as its first positional argument, accepts optional context filters, and returns a sequence of candidate document mappings. The current FAISS implementation also accepts `k` and supports `index_documents`; those are adapter capabilities, not requirements on injected test retrievers.

### Candidate document shape

The application accepts both ingestion-style documents (`text` plus nested `metadata`) and persisted-index documents (`text` with metadata fields beside it). Candidates are untrusted until the authorization and scope checks pass. A source record must not self-approve during ingestion.

### Request state

The caller owns a mutable session mapping and passes it to `handle_request`. The current orchestrator mutates recognized region/climate values and clears contradicted/ambiguous values. State is process-local in `main.py`; SQLite persistence is not part of this contract.

### Evidence and response

Retrieved content is a candidate, not authority. The curation registry binds an approved record to exact excerpt text and source/crop/review metadata. Scope checks run before display. The current response is a Portuguese string: clarification, literal excerpt with a cautionary header, or fail-closed response. No source means no agronomic answer.

### Reviewer verification

`tools.review_verifier` owns reusable review comparison/validation logic. `tests/verify_agronomist_reviews.py` remains a compatibility CLI/re-export surface; production modules must not import test modules. Agreement between AI reviewers is evidence about the recorded review artifacts, not a claim of professional certification or global agronomic precision.

## Target architecture (incremental, not yet implemented)

```text
Knowledge Preparation → Versioned Knowledge Base → Retrieval Engine
                                                    │ candidates + scores
Query → Context Engine ─────────────────────────────┤
                                                    ▼
Farm Memory (provenanced, expiring) → Safety Engine → Application Orchestrator
                                               ├── deterministic tools
                                               ├── optional language layer
                                               └── UI adapter
                                                    │
                                     cited response or explicit safe state

Update System: signed manifest, validated delta, rollback
Diagnostics: local, privacy-scoped, no hidden telemetry
```

The future Context Engine should request only fields required by an intent. Farm Memory must retain source, confirmation and validity information and must not silently promote stale values to current facts. Deterministic tools may calculate only from validated inputs linked to applicable evidence. Optional language models may interpret or explain cited material, never originate agronomic facts or select a dose/product/diagnosis.

## Dependency direction

```text
presentation → application → (context policy, safety policy, retriever port)
infrastructure adapters → domain contracts
knowledge preparation → domain contracts / retrieval adapter
tests → production modules
production modules ↛ tests
```

This phase corrects the concrete runtime-to-tests import in curation validation. It does not extract all policy out of `Orchestrator`; that remains a later Context/Safety Engine phase with a separately approved regression plan.

## Documentation authority

| Classification | Documents | Use |
|---|---|---|
| CURRENT | `ARCHITECTURE.md`, `BASELINE_REPORT.md`, `PROJECT_STATUS.md`, `SECURITY.md`, `KNOWLEDGE_PIPELINE.md`, `GOLDEN_SET_POLICY.md`, `RETRIEVAL_EVALUATION.md`, `MINING_GUIDE.md`, `docs/runtime_policy.md` | Implemented behavior, current policy and verified limits |
| DESIGN / ROADMAP | `ROADMAP.md`, `docs/product_readiness_plan.md`, `docs/slm_evaluation.md`, mobile specifications | Future proposals only; not evidence of implementation |
| HISTORICAL / EXPERIMENTAL | `CONCEPT.md`, `SDD.md`, `docs/golden_set_policy.md`, source-lead and corn MVP draft documents, research notes, scripts named `final_*` or `audit_runner_*` | Preserve context; where they conflict with current code and policies, they are not the runtime contract |

## Non-goals of this phase

No source is approved and no agronomic truth is invented. Retrieval filtering now expands beyond the previous fixed `k*10` candidate window when metadata filters exclude initial hits; returned vector hits include their distance. This mechanics change is regression-tested but does not establish semantic relevance. Android, Phi-3/MLC, STT/TTS and generative SLM work remain out of scope.
