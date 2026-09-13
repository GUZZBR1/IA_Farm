# 🌾 Field Deployment Guide: IA_Farm (AgriBrain Local)

This guide provides step-by-step instructions for deploying the IA_Farm autonomous AI specialist onto an Android device using Ollama or MLC LLM.

## 🚀 Overview
IA_Farm is designed for offline-first agricultural assistance. It utilizes a quantized Phi-3 model and a local Vector Database to provide expert knowledge without requiring an internet connection in the field.

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
   git clone https://github.com/[your-repo]/IA_Farm.git
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
   Ensure your indexed agricultural knowledge base is placed in the `/data/vector_index` directory (or the path specified in your config).

### 4. Execution
Run the main application:
```bash
python main.py
```

---

## ⚠️ Troubleshooting

### RAM & Memory Issues
If the application crashes due to "Out of Memory" (OOM) or becomes sluggish:
- **Enable mmap optimization:** The project includes a `memory_manager.py` tool. Ensure that the `mmap` flag is enabled in the configuration to map the model weights directly from disk rather than loading them entirely into RAM.
- **Weight Sharding:** For devices with < 6GB RAM, refer to the weight-sharding strategy in the documentation to load the model in smaller segments.

### API Key Configuration (Hybrid Mode)
While IA_Farm is offline-first, it supports **OpenRouter** as a fallback for complex queries.
1. Create a `.env` file in the root directory.
2. Add your key:
   ```env
   OPENROUTER_API_KEY=your_key_here
   ```
3. The system will automatically switch to fallback if the local model confidence is too low.

---

## 📋 Deployment Checklist
- [ ] Ollama/MLC LLM installed and running.
- [ ] Phi-3 model pulled and verified.
- [ ] Vector index placed in the correct directory.
- [ ] `requirements.txt` dependencies installed.
- [ ] (Optional) OpenRouter API key configured.
