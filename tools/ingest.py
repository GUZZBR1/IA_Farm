"""Parse Markdown sources into unapproved candidate documents."""

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
    parser = argparse.ArgumentParser(description="Parse local Markdown into unapproved candidates")
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/knowledge_candidates.json"))
    args = parser.parse_args()
    documents = ingest_paths(args.sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": 1, "status": "CANDIDATE",
                                      "promotion_allowed": False, "records": documents},
                                     ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(documents)} candidate documents to {args.output}; no index was built")


if __name__ == "__main__":
    main()
