# Source acquisition and evidence packaging

Status: **SOURCE ACQUISITION EXECUTED FOR PRIORITY CANDIDATES** (2026-10-01). Eight source documents/pages and five Embrapa repository license metadata pages were fetched over HTTPS, returned HTTP 200, MIME-checked, SHA-256 hashed, and stored as content-addressed local snapshots. Public Git tracks manifests only; source bytes and review exports remain local and ignored.

## Operational queue

The current queue is `tests/agronomic_candidate_queue.json`; its per-candidate source choices, snapshot hashes, locators, blockers and package references are mirrored in `data/source_discovery_report.json`. `python -m tools.build_candidate_queue` rebuilds the original intake queue from frozen inputs and therefore intentionally removes run-specific acquisition results; do not run it over the current queue without regenerating the evidence report. No entry is approved.

| Queue | Count | Work needed |
|---|---:|---|
| `SNAPSHOT_MISSING` | 6 | Six pest candidates remain without acquired source bytes. |
| `EVIDENCE_INSUFFICIENT` | 1 | Storage has a 2015 source snapshot, but its second cited source and case-specific evidence are missing. |
| `READY_FOR_HUMAN_REVIEW` | 11 | Local packages bind exact evidence/locators to immutable snapshots. This is not approval or permission to redistribute. |

All 18 remain unapproved and unpublished. Ten candidates have source material marked `RESTRICTED` for product distribution because their captured Infoteca record says CC BY-NC-ND 4.0 and app redistribution/adaptation rights were not established. Eight remain `UNKNOWN` (six pest candidates plus two MAPA/ZARC cases); UNKNOWN blocks publication but does not prevent a local professional review. `data/source_discovery_report.json` distinguishes captured evidence from frozen references and AI-review disagreements.

## Snapshot store

Captured source artifacts: Embrapa soil management, fertility/soil analysis, irrigation, maize physiology CT76, and harvest/post-harvest chapters; MAPA ZARC overview and Mato Grosso listing pages; Portaria SPA/MAPA 326 (maize second crop MT, 2026/27). Five Infoteca record pages containing explicit CC BY-NC-ND 4.0 notices were also frozen as separate license-evidence snapshots. Direct source references, final URLs, MIME, sizes, retrieval time, version, license note, and SHA-256 are in `data/source_registry/`. Snapshot blobs stay under ignored `data/source_snapshots/`.

`tools.source_snapshots.capture_snapshot` stores immutable, content-addressed bytes. `tools.register_source_snapshot` registers operator-acquired bytes and never fetches URLs. It now records final URL, safe filename, acquisition method and license evidence, and rejects common PDF/HTML MIME mismatches. Re-fetching changed bytes produces a new hash; never overwrite an older snapshot. A hash checks integrity only, not truth or authority.

Required metadata include `snapshot_id`, source ID, URL, retrieval time, hash, MIME type, size, title, institution, publication date/version, license status, relative artifact path, and snapshot status. Do not set a publication date/version unless the source itself establishes it.

## Evidence locators

`validate_locator` accepts a page, page range, section, table, figure, paragraph, heading, or document fragment, optionally with `quote_hash`. A locator is not valid evidence until a reviewer verifies it against the exact frozen snapshot. Keep page numbering conventions explicit (printed page vs PDF page index) in the evidence package. Quote text is supporting aid; page/section identity and snapshot hash remain necessary.

## License status

Allowed values: `UNKNOWN`, `LINK_ONLY`, `REDISTRIBUTION_ALLOWED`, `ATTRIBUTION_REQUIRED`, `RESTRICTED`, `PUBLIC_DOMAIN`. License determines distribution treatment, not agronomic correctness. Candidate hints about CC BY-NC-ND are not a completed rights review. `UNKNOWN`, `LINK_ONLY`, and `RESTRICTED` block inclusion of source-derived text in the published corpus. Retain an external link when policy permits; do not redistribute a source merely because it is publicly accessible.

For a published record, license evidence must also be retained and hash-verified. `ATTRIBUTION_REQUIRED` needs explicit attribution. The Infoteca record pages state CC BY-NC-ND 4.0; that does not settle whether IA_Farm may redistribute source-derived content. Therefore captured Embrapa material is restricted to local review while product rights remain unresolved. MAPA materials stay UNKNOWN because an explicit reuse license was not found in this captured source set. No legal conclusion is made.

## Group-specific acquisition blockers

- **ZARC-001:** overview page captured and paragraph located; human reviewer should check the generic framing against the intended season.
- **ZARC-002:** official MT listing, Portaria 326 and its amendment notice frozen. Candidate lacks municipality and required selection context, so packet is for clarification/abstention review only.
- **IRR-001/002:** a 2015 Infoteca chapter is captured. Its equivalence to the original AINFO reference is not assumed; packages highlight local inputs and historical scope.
- **PEST-001/002/003/006:** register the exact reviewer-cited 2021 cartilha where missing; the protocol repository landing page is not the same evidence artifact.
- **PEST-004:** no product registration/dose evidence is present; this phase does not acquire or recommend a product.
- **PEST-005:** source title indicates integrated braquiaria while the candidate says monoculture; reviewer must resolve scope or request a separately versioned candidate.
- **WATER-003:** the frozen CT76 PDF is locatable; the different HTML source cited by one AI reviewer remains missing. This is still an AI-review disagreement, not a demonstrated source conflict.
- **STORAGE-001:** newer 2015 harvest/post-harvest chapter is captured, but the cited 2013 source and a precise candidate locator remain unverified.

## Next operator action

Give the local packages in `human_review_packages/local/` to a qualified maize agronomist. Before sharing, confirm that the recipient and review context fit the source's noncommercial/no-derivatives terms. Review packages do not approve content; publication remains blocked by the license policy and qualified human promotion gate.
