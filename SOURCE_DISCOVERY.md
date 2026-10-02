# Source discovery and evidence results

Date: 2026-10-01  
Baseline: `ac9c3cd2220cf43b3cae8b4f4c1615ef712b0885`

The run prioritized source acquisition for maize MVP candidates. It acquired eight source documents/pages and five repository license metadata pages. Every acquired item returned HTTP 200; PDF/HTML signatures were checked; manifests record the requested and final URL, MIME, byte size, acquisition method and SHA-256. Source bytes are content-addressed under ignored `data/source_snapshots/`; tracked manifests are under `data/source_registry/`.

This establishes provenance and exact bytes. It does not establish agronomic correctness, current local applicability, or permission to redistribute source-derived material.

## Priority groups

| Priority | Candidates | Reason |
|---|---|---|
| P1 | SOIL-001, SOIL-002, FERT-001, PHENOLOGY-001, HARVEST-001, HARVEST-002 | Core maize explanations with identifiable Embrapa primary documents and candidate source/locator hints that could be checked against a snapshot. |
| P2 | ZARC-001, ZARC-002, IRR-001, IRR-002, WATER-003, STORAGE-001 | Useful topics with annual or local context requirements, older material, alternate source references, or unresolved AI interpretation. |
| P3 | PEST-001, PEST-002, PEST-003, PEST-004, PEST-005, PEST-006 | Higher-risk pest/diagnostic/product claims; exact cited documents are absent, and a product/dose claim lacks registration evidence. |

Priority is operational only. It is not a truth or safety rating.

## Acquired sources

| Captured document/page | Snapshot manifest | Notes |
|---|---|---|
| Embrapa, *Manejo de solos*, 9th ed., 2015 | `data/source_registry/EMBRAPA-CULTIVO-MILHO-SOLO-2015/` | PDF pages 2–3 checked for SOIL-001/002; CC BY-NC-ND 4.0 metadata frozen separately. |
| Embrapa, *Fertilidade de solos e adubação*, 9th ed., 2015 | `data/source_registry/EMBRAPA-MILHO-FERTILIDADE-2015/` | PDF p. 3 checked; replaced a mutable, unpinned landing-page hint for review. No dose selected. |
| Embrapa, *Irrigação*, 9th ed., 2015 | `data/source_registry/EMBRAPA-MILHO-IRRIGACAO-2015/` | PDF pp. 3 and 12 checked; equivalence to the older frozen AINFO reference is not assumed. |
| Embrapa, *Fisiologia da Produção de Milho*, Circular Técnica 76, 2006 | `data/source_registry/EMBRAPA-FISIOLOGIA-MILHO-2006/` | PDF pp. 2 and 7 checked; older material flagged for currentness review. |
| Embrapa, *Colheita e pós-colheita*, 9th ed., 2015 | `data/source_registry/EMBRAPA-MILHO-COLHEITA-2015/` | PDF pp. 3, 9 and 28 checked; newer than the candidate's 2009 source hint. |
| MAPA ZARC overview and Mato Grosso listing, captured 2026-10-01 | `data/source_registry/MAPA-ZARC-GENERAL-PAGE/`, `data/source_registry/MAPA-ZARC-MT-LISTING-2026/` | Frozen HTML; not sufficient alone for a municipality-specific date. |
| MAPA Portaria SPA/MAPA 326, maize second crop, Mato Grosso, 2026/27 | `data/source_registry/MAPA-ZARC-MT-2026-POC4001/` | Seven-page PDF captured 2026-10-01. Page 3 notes a later cultivar update; reviewer must verify current applicability. |

Five Infoteca record pages were also captured as license evidence for the five Embrapa PDFs. Each explicitly displays Creative Commons Attribution-NonCommercial-NoDerivatives 4.0. That notice is conservatively recorded as `RESTRICTED` for IA_Farm app distribution until product rights are reviewed. The review does not assume that public access authorizes app redistribution.

## Source choice and alternatives

- For FERT-001, the unversioned mutable planning page was not used as the evidence artifact. A frozen 2015 Embrapa chapter on soil fertility/adubation was selected; its age and regional limits remain for the reviewer.
- For IRR-001/002, the frozen candidate points to a separate AINFO PDF. A 2015 Infoteca irrigation chapter was acquired because it has an exact edition and locator. Equivalence between those files is not assumed.
- For HARVEST-001/002, the 2015 Embrapa chapter was selected over the older 2009 candidate reference. The 2009 bytes were not acquired; reviewer may ask for a new candidate revision if the specific older edition matters.
- For ZARC-002, the official listing and directly linked 2026/27 ordinance were captured. The candidate omits municipality and other selectors, so the package asks the professional reviewer to assess clarification/abstention; it contains no planting date.
- For pest cases, no candidate was promoted to the acquisition queue in this pass. Exact FAQ/cartilha identities and diagnostic/product evidence remain outstanding.

Per-candidate URLs, source selection, locator status, license status, conflict notes and exact blockers are in `data/source_discovery_report.json`; topic-level totals are in `SOURCE_COVERAGE.md`.

## AI disagreement handling

All five previously labeled conflicts remain disagreements between AI assessments, not demonstrated contradictions between agronomic sources. SOIL-002 and WATER-003 now have source-bound local packets; WATER-003's alternate HTML citation is still missing. PEST-002, PEST-005 and STORAGE-001 remain blocked by unacquired/uncertain source identity. No agent vote was used to resolve any item.

## Human review

Eleven Markdown/JSON packages are ready for qualified review under `human_review_packages/local/`. They are ignored by Git because they include source-derived excerpts and rights for redistribution/adaptation have not been established. A tracked index with package hashes is `data/human_review_package_index.json`. **READY_FOR_HUMAN_REVIEW is not APPROVED. Approved knowledge remains zero.**
