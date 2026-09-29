# Mobile optimization status

This document records validation work still required; it does not claim that
`mmap`, context caching, or Android memory optimization is implemented.

## Current runtime constraints

- The application response path uses deterministic rules and displays reviewed
  local excerpts. No generative language model runs on the phone.
- The current optional FAISS retriever uses a local Sentence-Transformers
  embedding model. Model packaging, cold-start memory, CPU latency, and truly
  offline startup have not been validated on Android.
- The `MemoryManager` currently handles SQLite user/session data. It does not
  provide the mmap or retrieval-cache APIs described in earlier drafts.

## Required device validation

On the target Android device, record the OS/device model, RAM, index size,
embedding model availability, cold/warm query latency, peak process memory,
thermal behavior, battery use, and behavior under memory pressure. Repeat with
network disabled and after process restart. The desktop test harness cannot
substitute for these measurements.

Do not claim `mmap`, model quantization, cache hit improvements, or a memory
budget until the implementation exists and the measurements are reproducible.
