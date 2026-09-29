# LLM validation checklist

The repository can validate orchestration without a live model by injecting a
fake retriever and a deterministic `_call_llm` function. This is what the core
tests and Golden Set do. A live-model run is a separate acceptance gate.

## Local Ollama

1. Start Ollama and confirm the selected model is available.
2. Build the local index with `python -m tools.ingest docs/corn_mvp/dataset_v0.1.md`.
3. Run `python main.py` and issue a general retrieval query.
4. Issue a technical dosage query without region/climate and confirm the model
   is not called and the application asks for the missing metadata.
5. Issue a technical query with metadata and confirm the answer is grounded in
   retrieved context.

## OpenRouter fallback

Set `OPENROUTER_API_KEY` in the process environment only. Never put a live key
in `.env.example`, test fixtures, logs, or GitHub source. Verify that Ollama is
unavailable, the fallback request succeeds, and the key is not printed.

## Evidence to record

For each model/runtime combination record model name, repository commit, source
index version, latency, failure behavior, and whether a qualified agronomist
reviewed the answer. A successful API call alone is not agronomic validation.
