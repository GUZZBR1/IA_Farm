# 🌾 Field Deployment Guide: IA_Farm (AgriBrain Local)

This guide provides the current deployment path for the IA_Farm offline-first
baseline. Android and field deployment remain experimental and require hardware
validation before production use.

## 🚀 Overview
IA_Farm is designed for offline-first agricultural assistance. It uses a local
vector database and can call a configured local Ollama runtime. OpenRouter is an
explicit optional fallback; it is never configured in source code.

---

## 🛠️ Installation & Setup

### 1. LLM Runtime Installation
Depending on your device capabilities, choose one of the following runtimes:

#### Option A: Ollama (via Termux) - *Easier Setup*
1. Install **Termux** (from F-Droid).
2. Update packages: `pkg update && pkg upgrade`
3. Install Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
4. Start the Ollama server:
   ```bash
   ollama serve
   ```

#### Option B: MLC LLM - *Higher Performance (GPU)*
1. Install the **MLC LLM** Android APK.
2. Follow the hardware-specific compilation pipeline detailed in `docs/mlc_llm_integration.md` to ensure Vulkan/OpenCL acceleration is active for your chipset.

### 2. Environment Setup
1. Clone the IA_Farm repository:
   ```bash
   git clone https://github.com/GUZZBR1/IA_Farm.git
   cd IA_Farm
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Model & Index Loading
1. **Load Phi-3 Model:**
   If using Ollama, run:
   ```bash
   ollama run phi3
   ```
2. **Prepare Vector DB:**
   Build the local index from the curated Markdown dataset:
   ```bash
   python -m tools.ingest docs/corn_mvp/dataset_v0.1.md
   ```
   The index is written to `data/vector_index`.

### 4. Execution
Run the main application:
```bash
python main.py
```

---

## ⚠️ Troubleshooting

### RAM & Memory Issues
If the application crashes due to "Out of Memory" (OOM) or becomes sluggish:
- The current `memory_manager.py` stores SQLite conversation/profile data; it
  does not implement model mmap or weight sharding.
- Use a smaller local model and validate memory consumption on the target device.
- Treat mobile support as experimental until the benchmark and OOM tests pass.

### API Key Configuration (Hybrid Mode)
While IA_Farm is offline-first, it supports **OpenRouter** as a fallback for complex queries.
1. Export the key in the shell (or load it with your process manager):
   ```env
   export OPENROUTER_API_KEY=your_key_here
   ```
3. The system switches to the fallback only when Ollama is unavailable and the
   environment variable is present. It does not infer model confidence.

---

## 📋 Deployment Checklist
- [ ] Ollama/MLC LLM installed and running.
- [ ] Phi-3 model pulled and verified.
- [ ] Vector index placed in the correct directory.
- [ ] `requirements.txt` dependencies installed.
- [ ] (Optional) `OPENROUTER_API_KEY` configured outside the repository.

For a demo without model dependencies, use `IA_FARM_MOCK=1 python main.py`.
This mode is not a production RAG or agronomic validation path.
