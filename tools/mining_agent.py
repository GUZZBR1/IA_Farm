"""Command-line entry point for indexing curated local knowledge."""

import argparse
from pathlib import Path

from tools.ingest import ingest_paths
from tools.vector_db import LocalVectorDB


def mine_knowledge(sources: list[Path], index_path: str = "data/vector_index") -> int:
    documents = ingest_paths(sources)
    if not documents:
        raise ValueError("No source documents were found")

    db = LocalVectorDB(index_path=index_path)
    db.index_documents(documents)
    return len(documents)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index curated IA_Farm knowledge")
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--index-path", default="data/vector_index")
    args = parser.parse_args()
    count = mine_knowledge(args.sources, args.index_path)
    print(f"Indexed {count} source documents into {args.index_path}")


if __name__ == "__main__":
    main()
