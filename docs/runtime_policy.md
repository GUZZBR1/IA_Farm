# Runtime policy: no generative LLM

The current application response path intentionally does not call Ollama,
OpenRouter, MLC LLM, or any other generative model. Intent checks, metadata
handling, safety gates, response formatting, and calculations are deterministic.
A local embedding model may be used only to retrieve passages; it does not
generate answers.

The optional FAISS retriever currently uses Sentence-Transformers embeddings.
Their offline packaging, cold-start memory and CPU latency still need validation
on the target Android device. If the product requirement is no ML model of any
kind, including embeddings, replace the retriever with lexical lookup.

Document extraction, when assisted by a model during knowledge preparation,
must stay outside the installed phone runtime. Every imported agronomic record
requires provenance, a valid review date, and a completed two-agent evidence
review against official sources before the application displays it. There is no
mandatory human agronomist approval gate; unresolved or conflicting evidence
must remain pending and unavailable to users.

Markdown metadata is untrusted input: ingestion always marks records pending
and ignores source identity, reviewer and approval claims from the document.
The runtime now requires an exact excerpt hash and matching record in
`data/curation_registry.json`; metadata alone cannot authorize display. Run
`python -m tools.curation_registry` to validate linked frozen input, both AI
review artifacts, their shared hash, excerpt-level hashes, official-source
agreement and comparison artifact before release. The registry is intentionally
empty: the 18 existing candidate reviews lack excerpt-level hashes and contain
five case disagreements. Do not manually mark records approved or use this
build for agronomic beta responses until reviewed excerpts are admitted through
that checked registry workflow.

The deterministic simulation and synthetic fixtures do not establish agronomic
correctness, field safety, or mobile performance. Those require approved
sources and tests on the physical target device.

An exploratory on-device SLM evaluation is documented in
`docs/slm_evaluation.md`. It is a proposal only and does not change the current
deterministic runtime policy.
