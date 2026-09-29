# 📘 Software Design Document (SDD) & Research Plan

**Runtime decision:** the application does not use a generative LLM on the
phone. Intent detection, guided questions, safety checks, response formatting,
and arithmetic are deterministic. Local embeddings may be used only to retrieve
curated passages; they do not generate answers. Any vision-assisted extraction
is knowledge-preparation work, never a phone runtime dependency.

## 1. System Architecture
The system follows a high-efficiency "Hybrid-Local" approach, designed for high-risk agricultural environments where reliability is non-negotiable.

### Phase 1: Knowledge Engineering (The Library)
*   **Curation Pipeline:** 
    - **Ingestion:** Convert source manuals into structured JSON/Markdown during knowledge preparation; assisted extraction, if used, must be reviewed before import.
    - **Verification:** Double-Verification via outlier detection (standard deviation) for numeric doses.
    - **Triangulation:** Cross-referencing multiple sources (e.g., EMBRAPA vs Company Manuals) to ensure semantic accuracy.
*   **Structuring:** Metadata tagging by region, climate, and crop type to prevent regional misapplication.

### Phase 2: The Intelligence Layer (The Brain)
*   **Intent Classifier (Efficiency):** Deterministic rules route queries into a guided flow and require region, climate and other fields before technical lookups.
*   **Hybrid Local RAG (Precision):**
    - **Vector Store:** Local FAISS/ChromaDB with metadata filtering.
    - **JSON-Pairing:** Critical dosage data is stored as deterministic JSON pairs; the runtime displays reviewed source data without generating or inferring recommendations.
    - **Guided Interface:** A "decision-tree" chat flow that guides the user to provide precise symptoms, reducing input noise.
*   **Deterministic Computation (Safety):** A Python function performs arithmetic only on a dose already validated by an approved source and qualified agronomist. It does not select or infer the dose.

### Phase 3: Mobile Deployment
*   **Optimization:** Measure the local retrieval index and embedding runtime against 2-4GB devices; do not claim quantization or mmap until implemented and measured.
*   **Edge Latency:** Evaluate a deterministic common-query cache only after correctness and invalidation rules are defined.
*   **Safety Layer:** Mandatory warnings for chemical applications and a "Conflict Alert" when sources diverge.

## 2. Detailed Research Plan
| Milestone | Focus Area | Key Deliverable |
| :--- | :--- | :--- |
| **M1** | **Dataset** | Curated Corn (Milho) dataset with JSON-Pairing and metadata. |
| **M2** | **Hardware** | Latency/RAM benchmark on Android 10 (4GB RAM). |
| **M3** | **Accuracy** | Zero-error validation for chemical dosage via Tool-use. |
| **M4** | **Offline** | Delta Update system for knowledge versioning. |

## 3. Risk Analysis
- **Unsupported advice:** Mitigation: do not generate recommendations; display only reviewed source excerpts with provenance.
- **Battery/Heat:** Mitigation: measure retrieval, memory and energy on a physical target phone before release.
- **Data Corruption:** Mitigation: implement and test hash-based verification for local index files.
- **Arithmetic Error:** Mitigation: use deterministic arithmetic only after an agronomist/source has approved the input dose.
