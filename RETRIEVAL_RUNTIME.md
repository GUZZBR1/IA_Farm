# Retrieval runtime reproducibility

Status: **capability and compatibility contracts implemented; real vector execution blocked by environment**.

## Dependency split

- `requirements-core.txt` describes lightweight application dependencies.
- `requirements-vector.in` describes the direct vector stack (`numpy==1.26.4`, `faiss-cpu==1.13.2`, `sentence-transformers==5.2.0`). It is **not a complete lockfile**: transitive dependencies, especially the CPU PyTorch build and Transformers stack, still need a resolved, platform-specific hash lock.
- Existing `requirements.txt` remains for compatibility with legacy installs. It still has broad ranges and should not be treated as a reproducible vector lock.

The current WSL environment has CPython 3.12.3, x86_64 Linux/glibc 2.39. NumPy 1.26.4 imports in system Python; FAISS, Sentence-Transformers, Torch, and Transformers do not. The project `.venv` lacks all five packages. `pip check` is clean only for that minimal environment. The working volume has sufficient disk according to the environment audit.

The immediate installation blocker is that WSL DNS lookup for `pypi.org` fails, while the Windows host can reach PyPI. This is not evidence that the platform is unsupported: the environment audit matched the published FAISS CPython 3.10+ manylinux x86_64 wheel tags to the current interpreter. The full transitive ML resolution and installation were not executed, so this is feasibility evidence only. Use a connected environment to resolve and hash-lock all transitive packages, download target-Linux wheels to a wheelhouse, then install in an isolated vector venv with `pip --no-index --find-links`. Do not change global DNS or install into system Python as a workaround.

## No automatic downloads

`LocalVectorDB` requires an existing local model directory and sets Sentence-Transformers `local_files_only=True`; model loading also accepts a pinned revision. Provide an explicit model manifest alongside the local artifact:

```json
{
  "model_id": "sentence-transformers/all-MiniLM-L6-v2",
  "revision": "immutable-hub-commit",
  "expected_dimension": 384,
  "artifact_origin": "verified local acquisition reference",
  "artifact_hash": "sha256 over deterministic local file inventory"
}
```

The example illustrates structure only; no model artifact has been downloaded or approved. The hash is computed over all local model files and relative paths. A missing model produces `MODEL_MISSING`; there is no implicit network fetch.

The implementation uses Sentence-Transformers' documented `revision` and `local_files_only` model-loading options ([official API reference](https://sbert.net/docs/package_reference/sentence_transformer/model.html)).

For the application, configure `IA_FARM_EMBEDDING_MODEL_PATH`, `IA_FARM_EMBEDDING_MODEL_ID`, `IA_FARM_EMBEDDING_MODEL_REVISION`, and `IA_FARM_KNOWLEDGE_RELEASE` to match the generated manifest. Do not point at a Hub name in place of a local path. The expected release must be pinned when loading a published index.

## Capability states

`python -m tools.vector_diagnostic --model PATH [--index PATH]` probes imports, Python/platform, PyPI DNS, pip consistency, disk availability, and the index sidecar without installing or downloading anything. Capability states are `AVAILABLE`, `DEPENDENCY_MISSING`, `MODEL_MISSING`, `INDEX_MISSING`, `INDEX_INVALID`, and `UNSUPPORTED_PLATFORM`. Diagnostics report failures without pretending that lexical results validate vectors.

The lexical path remains independent. Selecting `--backend lexical` is explicit and emitted as `LEXICAL_SELECTED_EXPLICITLY_BY_CALLER`; it is not a silent substitute for vector retrieval.

## Index compatibility

Published vector indexes are immutable and disposable. The authoritative input is the published knowledge store plus its release manifest. An index sidecar binds:

- index type;
- embedding model ID, immutable revision, dimension, origin, and artifact hash;
- knowledge release ID and record count;
- creation time;
- SHA-256 and byte size for `faiss.index` and `metadata.json`.

Each indexed document also carries the exact approved scope object and any source `valid_from`/`valid_until` dates. The runtime curation gate requires the scope object and flattened filter fields to match the frozen human-reviewed context, and rejects documents before `valid_from` or after `valid_until`.

`build_knowledge_index` requires a model manifest and writes `index_manifest.json`. `LocalVectorDB` refuses to load unversioned, corrupted, stale-release, wrong-model, wrong-revision, wrong-dimension, or changed-model-artifact indexes. Build a new index directory instead of mutating a published one. No compatible model, approved release, or real index is present today.

## Verified versus unknown

Verified: imports were probed in the named WSL environments; the vector packages were absent; WSL DNS failed; FAISS wheel-tag compatibility is plausible for the observed target.

Unknown: complete dependency resolution, disk footprint after installation, model artifact size/hash, actual FAISS import, real index build/load, semantic performance, and any agronomic retrieval quality. Linux results are not Android results.
