# Deployment guide: IA_Farm

The current response runtime is deterministic and does not use a generative
LLM, cloud endpoint, or LLM APK. Android deployment remains experimental and
must not be considered production-ready until physical-device validation is
complete.

## Local development

```bash
git clone https://github.com/GUZZBR1/IA_Farm.git
cd IA_Farm
python -m venv .venv
pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
python tests/run_golden_set.py
```

The optional local vector index uses FAISS and Sentence-Transformers embeddings
for retrieval; these embeddings do not generate answers. Build an index from
curated documents with:

```bash
python -m tools.ingest docs/corn_mvp/dataset_v0.1.md
```

Run the terminal application with `python main.py`. For a dependency-light demo,
`IA_FARM_MOCK=1 python main.py` uses the real deterministic orchestration logic
and an empty fixture database, so it will ask for context or fail closed.

## Android readiness

The repository does not yet contain a validated Android application package.
Before field use, validate local index/embedding packaging, offline startup,
RAM, latency, thermal and battery behavior on the target phone. `mmap`, model
quantization and cache improvements must not be claimed until implemented and
measured. See `docs/mobile_optimization.md` for the validation checklist.

## Knowledge safety

The application displays only excerpts with provenance, approved review status
and a valid review date. It does not calculate or choose an agronomic dose.
Existing example values in the dataset are not approved field guidance until a
qualified agronomist verifies the source and record.
