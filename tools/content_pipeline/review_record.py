"""Create an auditable human-review record for generated candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DECISIONS = {"needs-review", "approved", "rejected"}


def create_review_record(candidate_path: Path, batch_id: str, reviewer: str = "", decision: str = "needs-review", notes: str = "") -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {sorted(DECISIONS)}")
    candidate_path = Path(candidate_path)
    if not candidate_path.is_file():
        raise FileNotFoundError(candidate_path)
    return {
        "schemaVersion": "1.0.0",
        "batchId": batch_id,
        "candidateSha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        "reviewer": reviewer,
        "decision": decision,
        "notes": notes,
        "reviewedAt": datetime.now(timezone.utc).isoformat(),
        "publishedRequiresHumanApproval": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--decision", choices=sorted(DECISIONS), default="needs-review")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    record = create_review_record(Path(args.candidate), args.batch_id, args.reviewer, args.decision, args.notes)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Review record created: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
