# Golden Set policy

The Golden Set validates deterministic safety, metadata extraction, session
state, and source-display contracts. It contains no generated answers and must
not contain invented doses presented as authoritative.

The 165-battery simulation runs four scripted personas per case. Synthetic
fixtures are allowed only to test behavior and must be clearly labeled as test
data. They are not evidence of agronomic truth.

Recent additions cover inline corrections and negated context, common maize
agronomy wording that must trigger context collection, and ambiguous alternative
regions that must be clarified instead of guessed.

Production excerpts are displayed only when the record has non-empty text,
source provenance (`source_id` or `source`), an approved/validated review
status, a review date, and explicit maize/corn/milho crop scope. Even then, the
app displays the source excerpt verbatim; the system does not infer a diagnosis
or create a recommendation.

The runtime additionally requires an exact-text SHA-256 match against
`data/curation_registry.json`. Before release, run
`python -m tools.curation_registry`; it checks linked report/input hashes, both
review roles, same-case agreement and excerpt-level hash binding. The registry
is intentionally empty: existing reviews have no excerpt hashes and five
candidate cases disagree. Do not mark records approved manually.

Agronomic acceptance cases require source citations, crop and region metadata,
review date, claim-level evidence locators, and two independent AI evidence
reviews against official sources. Human agronomist validation is not required at
this stage and must not be implied by field names or benchmark output.
The repository currently does not have a production Golden Set, so agronomic
precision is not yet measured and the 95% target has not been demonstrated. The
numerical examples in `docs/corn_mvp/dataset_v0.1.md` must not be treated as
validated advice until they receive provenance and both source reviews.

The 95% target is intended to mean substantive answers factually supported by
official sources and applicable to the case. An unsupported or materially wrong
claim is incorrect. Coverage (answered cases), correct abstention, citation
fidelity, and critical dose/product errors must be reported separately; always
abstaining cannot satisfy the target. A synthetic behavioral pass rate or
agreement between AI reviewers is never, by itself, an agronomic accuracy score.

`tests/agronomic_benchmark.py` scores a frozen application run against cases
that have two independent AI evidence-review artifacts; it does not request or
imply human agronomist qualification. The active source-review flow is described
in `docs/agronomy_evidence_specialist.md` and `docs/agronomist_verifier.md`. The
checked-in `tests/agronomic_gold_set.json` is intentionally empty, so current
agronomic precision remains not measurable. Do not fill it with synthetic doses
or unreviewed internet snippets.

The scorer reports the observed precision and its one-sided exact 95%
Clopper-Pearson lower confidence bound. Passing the 95% target requires this
lower bound—not just the point estimate—to reach 95%. With no errors, at least
59 substantive, sufficiently distinct cases are needed; the set must also
cover the real maize question mix rather than repeat near-identical prompts.
The scorer requires a reviewer-assigned, unique `independence_group` for every
case; related wording variants must share a group and therefore cannot inflate
the independent sample count.

Source-backed drafts belong in `tests/agronomic_gold_candidates.json`, not the
scored set. Any case promoted into the runtime knowledge register must include
both independent AI review artifacts, official source IDs, exact evidence
locators, review date, scope, and the frozen report hash. Candidate claims in
that file are research leads, not approved answers or application knowledge.

To export a research packet for the two-agent source review, run:

```bash
python tests/export_agronomist_review.py
```

This writes `tests/agronomist_review_packet.md` with pending questions,
contexts, candidate claims, caveats and source evidence locations. The packet
does not approve cases or change the runtime knowledge base.

Promotion requires a specific question; `context` with `crop: maize`, region and
climate; a boolean `answerable`; expected claims; claim-level source evidence;
registered official source IDs; and `approval_status: approved` set only by the
controlled curation step after both AI reviews agree with evidence. The review
record must link both review artifacts, their common frozen-report SHA-256 and
an ISO review date, and must state that no human agronomist validation occurred.
Each source record must include title,
publisher, official HTTPS URL, source type, version/validity, precise locator
and retrieval date. Do not convert an agent's unsupported assertion into an
approved record.

Run the suite with:

```bash
python tests/run_golden_set.py
```

A green result does not measure Android hardware behavior or validate advice
for field use. It is not evidence that the 95% agronomic target has been met.
