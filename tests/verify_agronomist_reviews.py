"""Compatibility CLI for the production review-verification module."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.review_verifier import (  # noqa: E402
    OFFICIAL_DOMAINS,
    JUDGMENT_FIELDS,
    SOURCE_FIELDS,
    VERDICTS,
    compare_reviews,
    main,
    verify_report_file,
)

__all__ = [
    "OFFICIAL_DOMAINS",
    "JUDGMENT_FIELDS",
    "SOURCE_FIELDS",
    "VERDICTS",
    "compare_reviews",
    "main",
    "verify_report_file",
]


if __name__ == "__main__":
    raise SystemExit(main())
