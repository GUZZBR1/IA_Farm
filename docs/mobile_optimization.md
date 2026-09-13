# Mobile RAM Optimization Documentation

To ensure the IA_Farm system runs efficiently on Android devices with limited RAM (2GB-4GB), we have implemented two primary memory optimization techniques.

## 1. Memory-Mapped Files (mmap)

### The Problem
Loading large model weights or vector database indices directly into RAM using `read()` can lead to `OutOfMemory (OOM)` crashes, as the entire file must reside in the process's resident set size (RSS).

### The Solution
We use the `mmap` module in `tools/memory_manager.py`. Instead of reading the file into a buffer, `mmap` maps the file into the virtual address space. 
- **Demand Paging**: The OS only loads specific pages of the file from disk into RAM when they are accessed.
- **Shared Memory**: If multiple processes map the same file, they can share the same physical RAM pages.
- **Memory Pressure**: The OS can easily evict clean pages from RAM if other applications need memory, without needing a swap file.

### Implementation
Use `MemoryManager.mmap_load(path)` to obtain a memory-mapped view of the data.

---

## 2. Local Context Caching

### The Problem
Retrieving context via RAG (Retrieval-Augmented Generation) involves:
1. Embedding the user query (CPU/GPU intensive).
2. Searching the Vector DB (RAM/IO intensive).
3. Formatting the prompt.

Repeating this for common agricultural queries (e.g., "When to plant corn?") wastes resources and increases latency.

### The Solution
A simple key-value cache stores the hash of frequent queries and their corresponding retrieved context.
- **Hash-based Lookup**: Queries are hashed using SHA-256 to create unique, compact keys.
- **Persistence**: The cache can be persisted to a JSON file on disk to survive app restarts.

### Implementation
Use `MemoryManager.get_cached_context(query)` and `MemoryManager.set_cached_context(query, context)`.

## Benchmark Results
The `tests/ram_benchmark.py` script simulates these optimizations. 
- **Standard Load**: Increases RAM usage by approximately the size of the file.
- **mmap Load**: Minimal immediate RAM increase, as the file is mapped, not loaded.
- **Cache**: Reduces redundant RAG pipeline executions for repeat queries.
