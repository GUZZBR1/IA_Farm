# MVP maize source coverage

Coverage is based on the 18 frozen candidate questions. “Source snapshot” means at least one selected source artifact was acquired and hashed. It does not mean all references for a case were acquired, nor that the evidence is agronomically sufficient.

| Topic | Candidates | Source snapshots | Local review packages | Approved | Published |
|---|---:|---:|---:|---:|---:|
| Soil | 2 | 2 | 2 | 0 | 0 |
| ZARC | 2 | 2 | 2 | 0 | 0 |
| Fertilization | 1 | 1 | 1 | 0 | 0 |
| Irrigation | 2 | 2 | 2 | 0 | 0 |
| Pests | 6 | 0 | 0 | 0 | 0 |
| Phenology | 1 | 1 | 1 | 0 | 0 |
| Water stress | 1 | 1 | 1 | 0 | 0 |
| Harvest | 2 | 2 | 2 | 0 | 0 |
| Storage | 1 | 1 | 0 | 0 | 0 |
| **Total** | **18** | **12 candidate-linked sources** | **11** | **0** | **0** |

Thirteen immutable manifests are tracked: eight source documents/pages plus five Infoteca license metadata pages. The five license pages are evidence for rights status, not additional agronomic evidence. Raw source bytes and human review exports remain local under ignored paths.

## Remaining empty or incomplete areas

- **Pest management/diagnosis:** no official candidate-specific PDF/page snapshot. Product and dose evidence is entirely absent for PEST-004.
- **Storage:** the 2015 post-harvest chapter is captured, but the second cited source and a verified claim locator are missing.
- **ZARC-002:** current annual ordinance is captured, but municipality and other required selectors are absent from the question; no date is supplied.
- **Water stress:** one candidate source is captured and locatable. The distinct alternate source from an AI assessment remains unacquired, so the disagreement remains open.
- **License:** Embrapa source records declare CC BY-NC-ND 4.0 and are `RESTRICTED` for app distribution pending rights review. MAPA source records remain `UNKNOWN`.

Machine-readable coverage is `data/source_coverage.json`; package hashes and status are in `data/human_review_package_index.json`.
