# Technical debt register

This is a safe disposition list, not an authorization to delete historical evidence. Severity reflects risk to the next dependable maize MVP phase.

| Severity | Area / evidence | Consequence | Disposition |
|---|---|---|---|
| CRITICAL | No eligible production knowledge: empty registry and empty agronomic gold set; 0/9 local legacy chunks pass approval | Runtime cannot answer agronomic questions from an approved corpus | Maintain fail-closed behavior; Knowledge Engineering must create source-backed, explicitly reviewed records before promotion |
| HIGH | Historical credential-shaped values remain reachable in Git history; see `SECURITY.md` | Current-tree scan cannot prove revocation or history remediation | Maintain incident record; confirm provider rotation; coordinate any history rewrite |
| HIGH | Retrieval filters only a bounded vector candidate pool; similarity scores are discarded; no lexical comparison/threshold | Relevant eligible records may be missed or weak matches accepted | Refactor only after annotated retrieval evaluation; first add reproducible lexical/vector baseline |
| HIGH | FAISS index/metadata have positional coupling, no manifest/version/signature, and writes are not atomic (`tools/vector_db.py`) | Stale, mixed-generation or altered files may be difficult to detect | Design versioned manifest, atomic generation and integrity validation before corpus growth |
| HIGH | Local FAISS index is ignored and not reproducible from the official commit alone | Fresh checkout lacks this machine's vector artifact and embedding cache | Maintain source-of-truth documents and a reproducible rebuild; never commit unreviewed index as a shortcut |
| HIGH | Current metadata context is limited to hard-coded region/climate aliases (`tools/orchastrator.py`) | Requirements vary by intent, crop stage, soil, season and location | Refactor into Context Engine with per-intent requirements in a later phase |
| MEDIUM | Curation promotion path does not yet publish a canonical exact-chunk index generation | Approved registry records and built index can be managed inconsistently | Design an explicit raw→parsed→candidate→reviewed→approved→published workflow before adding content |
| MEDIUM | `CurationRegistry` has no all-or-nothing transactional persistence or signed registry source | A modified registry itself is not authenticated even though its referenced artifacts are hashed | Add signed manifest and atomic release later; the in-memory loader now clears all entries on malformed/duplicate records |
| MEDIUM | `MemoryManager` persists plaintext queries/history without retention, consent, expiry or provenance-state policy | Stale/sensitive farm data may be reused or retained unexpectedly | Keep disconnected from critical decision context until Farm Memory policy is implemented |
| MEDIUM | `DosageCalculator` is disconnected and validates only basic positive syntax; no unit conversion or finite-value contract | Callers could confuse arithmetic with agronomic selection or misuse units | Keep isolated; define typed/validated input contract before integration |
| MEDIUM | CI does not install retrieval dependencies, run real FAISS validation or invoke actual constrained CLI smoke | Green CI is narrower than full runtime evidence | Add separately provisioned retrieval and runtime smoke jobs without slowing contract suite unnecessarily |
| MEDIUM | `requirements.txt` has ranges, no environment lock; embedding model is named but not revision-pinned | Builds may vary and clean offline setup is not reproducible | Record tested dependency/model revisions and provide reproducible environment later |
| LOW | `tools/trainer.py` is named as training but performs four scripted heuristics; `tools/extractor.py` is a mock serializer | Misleading names can cause experimental helpers to be mistaken for product components | Deprecate names/docs; archive only after caller and evidence review |
| LOW | `tests/ram_benchmark.py` calls absent `MemoryManager` mmap/cache APIs | It cannot establish performance and is outside CI discovery | Mark experimental/obsolete; preserve until replacement evidence is recorded |
| LOW | `tools/vector_db.py` has a `__main__` demo that writes synthetic records to the default index | Running the module can contaminate a product index | Move demonstration to a temporary index in a future cleanup with regression coverage |
| LOW | Multiple `final_*`, `real_demo*`, and `audit_runner*` scripts overlap | Hard to identify authoritative verification entry points | Inventory and archive with provenance; do not delete reports or review artifacts automatically |

## Safe file dispositions

### Maintain

- `tools/orchastrator.py`, metadata canonicalization, exact curation checks and fail-closed responses.
- `tools/vector_db.py` as the current FAISS adapter while retrieval experiments are measured.
- Candidate source catalog, reviewer artifacts, empty gold set, and behavioral/regression tests; these are evidence, not noise.
- Explicit statements that simulation, reviewer agreement and Linux checks do not establish agronomic accuracy or Android readiness.

### Refactor next

- Context and safety policy out of the orchestration module, one behavior-preserving boundary at a time.
- Controlled knowledge publication, shared scope matching and reproducible index builds.
- Farm Memory only after consent, expiry, correction and provenance rules are agreed.
- Calculator only after validated inputs and unit contracts are specified.

### Deprecate or archive later

- Trainer/extractor/tagger prototypes and redundant `final_*` / demo runners once replacements and provenance are documented.
- Do not remove ignored data, review packets, candidate sources or history without a separate inventory and retention decision.

## Phase 2 changes in this commit series

- Add an explicit current/target architecture map and retriever protocol.
- Move review comparison into the production `tools/` package while preserving the old test CLI as a compatibility facade.
- Correct the mining guide so the unreviewed sample dataset is not presented as an input for production indexing.
- Make malformed/duplicate registry loading all-or-nothing and cover the valid-then-invalid sequence with a regression test.
- No feature that creates or publishes agronomic recommendations is added.

The former runtime→tests import and partial-load registry behavior are fixed in this phase; they are recorded here as resolved debt rather than open work.
