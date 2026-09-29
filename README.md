# 🌾 AgriBrain - AI Specialist for Agriculture

**AgriBrain** is an autonomous, offline-first AI specialist designed to bring precision agriculture to the field.

## Project Status: Corn MVP baseline in progress 🚧

The repository contains the initial RAG, ingestion and safety baseline. Mobile
hardening is still planned and is not yet validated on target hardware.

### Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py'
python -m tools.ingest docs/corn_mvp/dataset_v0.1.md
python main.py
```

For a demo-only run without model dependencies:

```bash
IA_FARM_MOCK=1 python main.py
```

## 🚀 Project guides

- **Implementation guide**: See `MINING_GUIDE.md`.
- **Project DNA**: See `CONCEPT.md` and `docs/agent_dna.md`.
- **Current status**: See `PROJECT_STATUS.md` and `ROADMAP.md`.
- **Operator map**: See `AGENTE.md`.
- **Deployment**: See `docs/deployment_guide.md`.
- **Golden Set policy**: See `docs/golden_set_policy.md` and run `python tests/run_golden_set.py`.
- **Persona simulation**: See `docs/test_environment.md` for the ten-battery user/agronomist harness.
- **LLM validation**: See `docs/llm_validation.md`.
- **Security response**: See `SECURITY.md`.

## 🛠️ Core technology

- **Llama/Phi-3 quantized** (core intelligence)
- **FAISS vector store** (technical knowledge)
- **Deterministic calculator** (zero-error arithmetic baseline)
- **RAG pipeline** (EMBRAPA/CIMMYT sources)

Every push and pull request runs the dependency-free test suite, Golden Set
guardrails, Python compilation and the tracked-file security scan through
GitHub Actions.

---
Developed by **guzzbr**
