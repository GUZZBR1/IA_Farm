# Human review workflow

Status: **DESIGN AND STRUCTURAL CONTRACTS**. There are no ready packets and no agronomic approvals. Human review is an external professional decision; software validates required records and bindings but cannot authenticate a person's identity or qualifications by itself.

## Flow

`source reference → immutable snapshot → parsed candidate → exact evidence locator → license decision → review package → qualified human decision → promotion gate → published knowledge`

No state may jump from a reference/raw source straight into a published corpus. The source snapshot and candidate content are both hashed. Any material change requires a new review against the new hashes.

## Review package

`tools.human_review.build_review_package` records the candidate/claim/context, source metadata, snapshot hash, candidate content hash, locator, exact evidence, conflicting evidence, risk class, reviewer questions, and a proposed decision. AI reviewer notes are annotated `origin=AI` and `not_human_review=true`; `proposed_decision` is explicitly a suggestion. Do not create an actionable review packet if evidence is absent. At present, all 18 remain blocked, so ready-to-sign packages count is zero.

## Human decision schema

Required fields: `reviewer_id`, `reviewer_role`, `qualification`, `reviewed_at`, `decision`, `scope`, `comments`, `source_snapshot_hash`, `candidate_content_hash`, `limitations`. The separate approval artifact also binds nullable `valid_from` and `valid_until`; retrieved index metadata must match those exact reviewed values.

Decision is one of `APPROVE`, `REJECT`, `NEEDS_CHANGES`, `INSUFFICIENT_EVIDENCE`, or `CONFLICT_REQUIRES_RESOLUTION`. `APPROVE` is accepted only when reviewer scope and both hashes exactly match the packet. The caller must separately verify the reviewer's identity/qualification and append the signed or authenticated review artifact to an append-only audit store. An ID string by itself is not identity proof.

## Internal risk review policy

| Internal risk tier | Minimum workflow |
|---|---|
| LOW | One qualified reviewer |
| MEDIUM | One qualified reviewer plus independent verification |
| HIGH | Two independent qualified reviewers plus verification |
| CRITICAL | Block publication until a product-specific policy is explicitly defined |

These are proposed internal product safeguards, not legal or regulatory requirements. The current lifecycle API does **not yet enforce risk-tier-specific reviewer counts**; it enforces the common explicit human approval, exact-content/snapshot binding, source, license, scope, and conflict gates. Do not treat HIGH or CRITICAL as publishable until a risk-tier review collection and its authenticated evidence are implemented and tested. This proposal never reduces the common gates.

## Conflicting evidence

`tests/agronomic_candidate_conflicts.json` records five unresolved AI-review disagreements and separates scope, date, region, method, and source-identity questions. It does not label them proven contradictions. If reviewer citations name a document absent from the candidate source list, register and capture that document before review. No majority vote among AI agents can resolve a conflict.

## Promotion gate

`tools.human_review.promotion_blockers` blocks publication unless the snapshot is present and valid; locator validates; license status and hashed license evidence are compatible; schema and scope are complete; exact human approval matches the candidate and snapshot hashes; no conflict blocks; and knowledge is neither expired nor deprecated. `knowledge_lifecycle` independently verifies snapshot and license artifact bytes, attribution where required, structured locator, and the existing human action artifacts. Risk-tier-specific reviewer counts remain a design item. The registry/store stay empty.

## Failure/correction semantics

Changed content or source hashes invalidate the prior review. Wrong scope or locator requires `NEEDS_CHANGES`; unresolved conflicts require `CONFLICT_REQUIRES_RESOLUTION`; missing/weak evidence requires `INSUFFICIENT_EVIDENCE`. A rejection does not delete history. A new candidate revision links to the prior item and proceeds through review again.
