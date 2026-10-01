# Golden Set policy

There are three distinct datasets. `tests/agronomic_gold_set.json` is the agronomic set and remains empty. `tests/agronomic_gold_candidates.json` is a frozen research lead set, not an answer key. `tools/retrieval_eval_dataset.json` contains only synthetic non-agronomic mechanics fixtures. Behavioral simulations remain a separate behavioral suite. Their scores must never be represented as agronomic accuracy or retrieval precision.

An agronomic case requires question, intent, context, scope, risk, required context, expected behavior, expected sources/record IDs, allowed and forbidden claims, abstention expectation, review status, review evidence and notes. `tests/schemas/agronomic_case.schema.json` defines the structure. A case can be `approved` only after traceable source snapshots, exact locators and a qualified human agronomic approval bound to the reviewed content. Consensus among agents is not approval.

The audit in `tests/agronomic_candidate_audit.json` records all 18 existing drafts: 5 are `CONFLICTING_EVIDENCE`; 13 are `INSUFFICIENT_EVIDENCE`. All lack retained source snapshots and qualified human approval. None is ready for scoring; none is approved. The prior comparison artifact's `human_approval_required:false` value is historical and superseded by this policy.

Negative tests may verify abstention when a source is absent, scope is incompatible, context is missing, evidence is expired or sources conflict. Such fixtures assert software behavior only and do not establish agronomic facts.

Report independently: context accuracy, source accuracy, abstention accuracy, scope accuracy, citation accuracy, retrieval recall/precision and unsafe-answer rate. Do not collapse these into a single score. Current approved-case count is zero, so agronomic metrics are **not measured**.
