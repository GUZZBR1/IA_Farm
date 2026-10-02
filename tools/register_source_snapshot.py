"""Register bytes acquired by an operator; this command does not fetch URLs."""

from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path

from tools.source_snapshots import capture_snapshot, write_public_manifest

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--institution", required=True)
    parser.add_argument("--publication-date")
    parser.add_argument("--version")
    parser.add_argument("--mime-type")
    parser.add_argument("--final-url")
    parser.add_argument("--acquisition-method", default="operator-provided-file")
    parser.add_argument("--license-status", default="UNKNOWN")
    parser.add_argument("--license-evidence-url")
    parser.add_argument("--license-evidence-note")
    parser.add_argument("--storage-root", type=Path, default=ROOT / "data/source_snapshots")
    parser.add_argument("--manifest-root", type=Path, default=ROOT / "data/source_registry")
    args = parser.parse_args()
    content = args.file.read_bytes()
    mime_type = args.mime_type or mimetypes.guess_type(args.file.name)[0] or "application/octet-stream"
    snapshot = capture_snapshot(
        source_id=args.source_id, original_url=args.url, content=content,
        mime_type=mime_type, document_title=args.title,
        institution=args.institution, publication_date=args.publication_date,
        document_version=args.version, final_url=args.final_url,
        filename=args.file.name, acquisition_method=args.acquisition_method,
        license_status=args.license_status, license_evidence_url=args.license_evidence_url,
        license_evidence_note=args.license_evidence_note,
        storage_root=args.storage_root)
    manifest = write_public_manifest(snapshot, manifest_root=args.manifest_root)
    print(json.dumps({"snapshot_id": snapshot["snapshot_id"],
                      "content_hash": snapshot["content_hash"],
                      "license_status": snapshot["license_status"],
                      "artifact_ref": snapshot["local_path"],
                      "manifest_path": str(manifest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
