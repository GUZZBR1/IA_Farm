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
requires provenance, a valid review date, and qualified specialist approval
before the application displays it.

The deterministic simulation and synthetic fixtures do not establish agronomic
correctness, field safety, or mobile performance. Those require approved
sources and tests on the physical target device.

An exploratory on-device SLM evaluation is documented in
`docs/slm_evaluation.md`. It is a proposal only and does not change the current
deterministic runtime policy.
