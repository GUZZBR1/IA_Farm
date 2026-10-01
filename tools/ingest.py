"""Turn curated Markdown knowledge into documents for the local vector index."""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
METADATA_RE = re.compile(r"\*\*Metadata:\*\*\s*(\{.*?\})", re.DOTALL)
TRUSTED_METADATA_FIELDS = {
    "source", "source_id", "review_status", "reviewed_at", "review_date",
    "reviewer", "reviewer_id", "approval_id",
}


def _sections(markdown: str) -> Iterable[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(markdown))
    if not matches:
        yield "document", markdown.strip()
        return

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        yield match.group(1).strip(), markdown[start:end].strip()


def parse_markdown_documents(path: str | Path) -> List[Dict[str, Any]]:
    """Parse each Markdown subsection into a text document with metadata."""

    source = Path(path)
    markdown = source.read_text(encoding="utf-8")
    documents: List[Dict[str, Any]] = []

    for title, section in _sections(markdown):
        if not section.strip():
            continue

        metadata: Dict[str, Any] = {
            "source": str(source),
            "section": title,
            # Source files are untrusted input; approval must come from a
            # separate curation process, never from the document itself.
            "review_status": "pending",
        }
        metadata_match = METADATA_RE.search(section)
        if metadata_match:
            try:
                parsed_metadata = json.loads(metadata_match.group(1))
                if isinstance(parsed_metadata, dict):
                    metadata.update({
                        key: value
                        for key, value in parsed_metadata.items()
                        if key.casefold() not in TRUSTED_METADATA_FIELDS
                    })
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid metadata JSON in {source}:{title}") from exc

        documents.append({"text": section, "metadata": metadata})

    return documents


def ingest_paths(paths: Iterable[str | Path]) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    for path in paths:
        documents.extend(parse_markdown_documents(path))
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Index curated IA_Farm Markdown knowledge")
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--index-path", default="data/vector_index")
    args = parser.parse_args()

    from tools.vector_db import LocalVectorDB

    documents = ingest_paths(args.sources)
    db = LocalVectorDB(index_path=args.index_path)
    db.index_documents(documents)
    print(f"Indexed {len(documents)} documents into {args.index_path}")


if __name__ == "__main__":
    main()
