# 🌽 Corn (Milho) Knowledge Map - MVP v1.0

## 1. Core Knowledge Modules
### Module A: Soil & Nutrition
- **Focus:** Liming (Calagem), NPK Fertilization, micronutrients.
- **Critical Data:** Dose tables based on soil analysis.
- **Format:** JSON-Pairing for dosage values.

### Module B: Planting & Management
- **Focus:** Planting window, spacing, seed depth, population density.
- **Critical Data:** Regional planting calendars.
- **Format:** Metadata tagged by region (State/Climate).

### Module C: Phytosanitary (Pests & Diseases)
- **Focus:** Spodoptera frugiperda (Fall Armyworm), Dalbulus maidis (Corn Leafhopper).
- **Critical Data:** Visual symptoms -> Diagnosis -> Chemical/Biological treatment.
- **Format:** Decision-tree (Guided Interface).

### Module D: Harvest & Post-Harvest
- **Focus:** Grain moisture, harvest timing, storage temperature.
- **Critical Data:** Moisture thresholds for storage.
- **Format:** Deterministic thresholds.

## 2. Data Ingestion Pipeline
1. **Source:** EMBRAPA / Technical Manuals.
2. **Processing:** Vision LLM -> JSON-Pairing -> Markdown.
3. **Verification:** Standard deviation check for numeric values.
4. **Deployment:** Vectorized into Local FAISS DB.
# HISTORICAL / UNVALIDATED KNOWLEDGE MAP

This map is not a source registry and its claim-like entries have not been
approved. Do not index it or use it as a source for Golden Set answers. Use the
current source-snapshot and human-approval gates documented in
`KNOWLEDGE_PIPELINE.md`.
