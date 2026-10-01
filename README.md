# 🌾 AgriBrain - AI Specialist for Agriculture

**AgriBrain** is a prototype for an offline-first agricultural assistant. Its
current response path is deterministic: it requests missing context, refuses
unreviewed data, and displays local excerpts without generating recommendations.

## Project Status: Corn MVP baseline in progress 🚧

The repository contains the initial RAG, ingestion and safety baseline. Mobile
hardening is still planned and is not yet validated on target hardware.

### Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py'
python main.py
```

Do not ingest `docs/corn_mvp/dataset_v0.1.md` as production knowledge: its
examples are unreviewed and not approved field guidance. Markdown ingestion now
marks all records pending; approval must come from a separate curation process.
For now, that curation process uses two independent AI evidence reviewers
against official primary sources; no human agronomist approval is required or
claimed. AI agreement is not professional certification or a global accuracy
measurement. Physical Android validation is the final readiness phase and has
not been completed.

For a demo-only run without model dependencies:

```bash
IA_FARM_MOCK=1 python main.py
```

## 🚀 Project guides

- **Official architecture**: See `ARCHITECTURE.md` for implemented boundaries and target layers.
- **Baseline and technical debt**: See `BASELINE_REPORT.md` and `TECH_DEBT.md`.
- **Implementation guide**: See `MINING_GUIDE.md`.
- **Project DNA**: See `CONCEPT.md` and `docs/agent_dna.md`.
- **Current status**: See `PROJECT_STATUS.md` and `ROADMAP.md`.
- **Operator map**: See `AGENTE.md`.
- **Deployment**: See `docs/deployment_guide.md`.
- **Golden Set policy**: See `docs/golden_set_policy.md` and run `python tests/run_golden_set.py`.
- **Persona simulation**: See `docs/test_environment.md` for the 165-battery, four-persona harness.
- **Runtime contract**: No generative LLM is used in the application response path.
- **Runtime policy**: See `docs/runtime_policy.md` for the embedding caveat and mobile limits.
- **Security response**: See `SECURITY.md`.

## 🛠️ Core technology

- **Deterministic rules and reviewed source excerpts** (core response path)
- **FAISS vector store** (local retrieval; uses embeddings, not text generation)
- **Deterministic calculator** (exact arithmetic on an already validated input)
- **Local retrieval** (candidate source catalog; no agronomic corpus is yet approved for public use)

Every push and pull request runs the dependency-free test suite, Golden Set
guardrails, Python compilation and the tracked-file security scan through
GitHub Actions.

---
Developed by **guzzbr**
