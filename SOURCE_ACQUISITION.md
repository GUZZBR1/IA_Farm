# Source acquisition and evidence packaging

Status: **OPERATING DESIGN + EMPTY SNAPSHOT STORE**. The repository contains references to documents, not captured evidence. No source URL was fetched or revalidated in this phase. Source references and narrative page hints do not prove ingestion, currentness, applicability, or license rights.

## Operational queue

Regenerate `tests/agronomic_candidate_queue.json` with `python -m tools.build_candidate_queue`. It is derived from the frozen candidate and audit inputs; it keeps `approved=false`, maps all source licenses to `UNKNOWN`, and marks locators as narrative hints until checked against bytes.

| Queue | Count | Work needed |
|---|---:|---|
| `SNAPSHOT_MISSING` | 13 | Acquire the exact identified source/version and freeze bytes before evidence review. |
| `EVIDENCE_CONFLICT` | 5 | Resolve AI-review disagreement and missing/different source identity; these are not established source contradictions. |
| `READY_FOR_HUMAN_REVIEW` | 0 | Requires snapshot, exact locator/evidence, license decision, scope, and complete review packet. |

All 18 also have `LICENSE_UNKNOWN`, no exact evidence hash, and no qualified human approval. Each candidate row names its source references, institution, frozen title/date hints, page/section hint, blockers, and a specific next action. The 2026-09-29 retrieval timestamps in source metadata are historical assertions and were not refreshed.

## Snapshot store

`tools.source_snapshots.capture_snapshot` stores immutable, content-addressed bytes and JSON metadata under `data/source_snapshots/<source_id>/<sha256>.*`. Snapshot bytes stay out of Git. `tools.register_source_snapshot` registers bytes that an operator already acquired; it never fetches a URL. It writes a public metadata manifest to `data/source_registry/<source_id>/<sha256>.json` for review/commit while the blob stays ignored. A same-content recapture is idempotent; different bytes create a new digest and `CHANGED_SINCE_PRIOR_SNAPSHOT`. `verify_snapshot` checks path containment, size, and SHA-256. A digest checks integrity only; it says nothing about truth or authority.

Required metadata include `snapshot_id`, source ID, URL, retrieval time, hash, MIME type, size, title, institution, publication date/version, license status, relative artifact path, and snapshot status. Do not set a publication date/version unless the source itself establishes it.

## Evidence locators

`validate_locator` accepts a page, page range, section, table, figure, paragraph, heading, or document fragment, optionally with `quote_hash`. A locator is not valid evidence until a reviewer verifies it against the exact frozen snapshot. Keep page numbering conventions explicit (printed page vs PDF page index) in the evidence package. Quote text is supporting aid; page/section identity and snapshot hash remain necessary.

## License status

Allowed values: `UNKNOWN`, `LINK_ONLY`, `REDISTRIBUTION_ALLOWED`, `ATTRIBUTION_REQUIRED`, `RESTRICTED`, `PUBLIC_DOMAIN`. License determines distribution treatment, not agronomic correctness. Candidate hints about CC BY-NC-ND are not a completed rights review. `UNKNOWN`, `LINK_ONLY`, and `RESTRICTED` block inclusion of source-derived text in the published corpus. Retain an external link when policy permits; do not redistribute a source merely because it is publicly accessible.

For a published record, the license decision also needs `license_evidence_ref` plus `license_evidence_sha256`; the lifecycle gate reads the artifact and verifies its bytes. `ATTRIBUTION_REQUIRED` also needs explicit attribution text. These fields do not authenticate the rights reviewer; that remains an operational verification step.

## Group-specific acquisition blockers

- **All 18:** capture exact bytes, verify title/version/publication metadata, determine applicable license, and replace broad narrative locator hints with snapshot-checked locators.
- **ZARC-001/002:** capture the exact current manual/ordinance and annex. The current listing page alone is not a season/municipality-specific evidence package.
- **IRR-001/002:** reconcile the cited PDF versus separately cited HTML page and establish source edition/date.
- **PEST-001/002/003/006:** register the exact reviewer-cited 2021 cartilha where missing; the protocol repository landing page is not the same evidence artifact.
- **PEST-004:** no product registration/dose evidence is present; this phase does not acquire or recommend a product.
- **PEST-005:** source title indicates integrated braquiaria while the candidate says monoculture; reviewer must resolve scope or request a separately versioned candidate.
- **WATER-003:** capture both PDF and separately cited HTML material and compare provenance, scope, and locator.
- **STORAGE-001:** reconcile the 2009/2013 candidate documents and the alternate reviewer citation before preparing a review packet.

## Next operator action

Acquire original source files through lawful channels; retain exact bytes and acquisition metadata; verify licensing; then attach exact locators/evidence. Only after those steps can `build_review_package` produce a packet fit for human review. Current candidate intake packages remain blocked and are not represented as ready for a reviewer.
