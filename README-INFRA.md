# Infrastructure and runtime notes

The repository keeps source documents and code under version control. Generated
embeddings are written to `data/vector_index/` and are intentionally ignored by
Git because they depend on the embedding model and can be rebuilt deterministically.

Install dependencies from `requirements.txt` in a virtual environment. If the
host has storage or network limits, configure those at the environment level;
the application itself uses paths relative to the repository and does not depend
on a developer-specific home directory or symlink.

To rebuild the local index:

```bash
python -m tools.ingest docs/corn_mvp/dataset_v0.1.md
```

Do not delete `data/` recursively as a recovery step. Inspect the target first
and remove only disposable generated files when necessary.
