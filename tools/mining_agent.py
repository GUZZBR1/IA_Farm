"""Parse local documents into candidate artifacts; never publish or index them."""

import argparse
from pathlib import Path

from tools.ingest import ingest_paths
import json


def mine_knowledge(sources: list[Path], output_path: str = "data/knowledge_candidates.json") -> int:
    documents = ingest_paths(sources)
    if not documents:
        raise ValueError("No source documents were found")

    # Parsing is not curation approval. Keep candidate data out of the runtime
    # retrieval index until it passes the explicit review/publication lifecycle.
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "schema_version": 1,
        "status": "CANDIDATE",
        "promotion_allowed": False,
        "records": documents,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(documents)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse local documents into non-published knowledge candidates")
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", default="data/knowledge_candidates.json")
    args = parser.parse_args()
    count = mine_knowledge(args.sources, args.output)
    print(f"Wrote {count} candidates to {args.output}; approval and index publication are separate steps")


if __name__ == "__main__":
    main()
