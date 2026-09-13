# 📘 Software Design Document (SDD) & Research Plan

## 1. System Architecture
The system follows a high-efficiency "Hybrid-Local" approach, designed for high-risk agricultural environments where reliability is non-negotiable.

### Phase 1: Knowledge Engineering (The Library)
*   **Curation Pipeline:** 
    - **Ingestion:** Using advanced Vision LLMs (GPT-4o/Claude 3.5) to convert legacy PDFs/images into structured JSON/Markdown.
    - **Verification:** Double-Verification via outlier detection (standard deviation) for numeric doses.
    - **Triangulation:** Cross-referencing multiple sources (e.g., EMBRAPA vs Company Manuals) to ensure semantic accuracy.
*   **Structuring:** Metadata tagging by region, climate, and crop type to prevent regional misapplication.

### Phase 2: The Intelligence Layer (The Brain)
*   **Intent Classifier (Efficiency):** Lightweight pre-processor to route queries.
    - *General:* Simple scripts.
    - *Technical:* Trigger SLM.
*   **Hybrid Local RAG (Precision):**
    - **Vector Store:** Local FAISS/ChromaDB with metadata filtering.
    - **JSON-Pairing:** Critical dosage data is stored as deterministic JSON pairs to eliminate LLM reading errors.
    - **Guided Interface:** A "decision-tree" chat flow that guides the user to provide precise symptoms, reducing input noise.
*   **Deterministic Computation (Safety):** 
    - **Tool-Use/Function Calling:** Calculation of dosages is outsourced to a deterministic Python function. The LLM extracts parameters, but a calculator performs the math to ensure 100% accuracy.

### Phase 3: Mobile Deployment
*   **Optimization:** 4-bit quantization and Memory Mapping (mmap) to fit in 2-4GB RAM.
*   **Edge Latency:** Pre-vectorized "common context" cache to avoid on-device embedding for frequent queries.
*   **Safety Layer:** Mandatory warnings for chemical applications and a "Conflict Alert" when sources diverge.

## 2. Detailed Research Plan
| Milestone | Focus Area | Key Deliverable |
| :--- | :--- | :--- |
| **M1** | **Dataset** | Curated Corn (Milho) dataset with JSON-Pairing and metadata. |
| **M2** | **Hardware** | Latency/RAM benchmark on Android 10 (4GB RAM). |
| **M3** | **Accuracy** | Zero-error validation for chemical dosage via Tool-use. |
| **M4** | **Offline** | Delta Update system for knowledge versioning. |

## 3. Risk Analysis
- **Hallucinations:** $ightarrow$ Mitigation: Strict RAG + Source Citation + Triangulation.
- **Battery/Heat:** $ightarrow$ Mitigation: Intent Classifier + Asynchronous execution.
- **Data Corruption:** $ightarrow$ Mitigation: Hash-based verification of local vector files.
- **Arithmetic Error:** $ightarrow$ Mitigation: Deterministic Tool-use (External Calculator).
