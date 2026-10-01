# Knowledge preparation guide — current limits

**Classification:** preparation-tool documentation. This is not a source approval policy or a promise that the full preparation pipeline is implemented. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the authoritative system map.

## Implemented path

`tools.ingest` parses local Markdown sections headed by `###`. It creates candidate records with `review_status: pending` and ignores source identity, reviewer and approval claims supplied inside Markdown. `tools.mining_agent` can pass those records to the local FAISS indexer. The tool does not fetch web pages, parse PDFs, perform OCR, or approve content.

The optional `tools.vision_extractor` is an experimental, remote OpenRouter helper. It is not called by ingestion or by the application response runtime and does not complete provenance or approval metadata.

## Safe scratch-index example

Only use a source that you are authorized to process. The following writes to a separate scratch index; it does not publish or approve the resulting records:

```bash
python -m tools.mining_agent path/to/candidate.md --index-path path/to/scratch-index
```

Do **not** use `docs/corn_mvp/dataset_v0.1.md` as production knowledge. It contains unreviewed numeric examples. Ingestion status remains pending, and the current runtime registry contains no approved excerpts. There is not yet a complete controlled command that promotes reviewed chunks and rebuilds a production index as one versioned release.

## Current validation commands

```bash
python -m tools.test_libs
python -m unittest discover -s tests -p 'test_*.py'
python -m tools.curation_registry
```

A passing unit suite or valid empty registry does not establish agronomic accuracy, source licensing, real FAISS quality, or Android readiness. See `BASELINE_REPORT.md` and `TECH_DEBT.md` for current evidence and gaps.
