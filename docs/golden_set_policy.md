# Golden Set policy

The Golden Set validates deterministic safety, metadata extraction, session
state, and source-display contracts. It contains no generated answers and must
not contain invented doses presented as authoritative.

The 100-battery simulation runs three scripted personas per case. Synthetic
fixtures are allowed only to test behavior and must be clearly labeled as test
data. They are not evidence of agronomic truth.

Production excerpts are displayed only when the record has non-empty text,
source provenance (`source_id` or `source`), an approved/validated review
status, and a review date. Even then, the app displays the source excerpt
verbatim; the system does not infer a diagnosis or create a recommendation.

Agronomic acceptance cases require a source citation, crop and region metadata,
review date, and approval from a qualified agronomist. The repository currently
does not have a fully approved production Golden Set. The numerical examples in
`docs/corn_mvp/dataset_v0.1.md` must not be treated as validated advice until
they receive provenance and specialist review.

Run the suite with:

```bash
python tests/run_golden_set.py
```

A green result does not measure Android hardware behavior or validate advice
for field use.
