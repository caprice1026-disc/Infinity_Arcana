"""Serializable reading records shared by UI and API adapters."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ReadingRecord:
    id: str
    request_version: str
    content_release_id: str
    seed: str
    spread_id: str
    draws: list[dict[str, Any]]
    schema_version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    locale: str = "ja-JP"
    question: str = ""
    category: str | None = None
    draw_policy_id: str = "balanced-two-stage-v1"
    draw_policy_version: int = 1
    random_algorithm: str = "sha256-counter-v1"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["schemaVersion"] = value.pop("schema_version")
        value["requestVersion"] = value.pop("request_version")
        value["contentReleaseId"] = value.pop("content_release_id")
        value["spreadId"] = value.pop("spread_id")
        value["createdAt"] = value.pop("created_at")
        value["drawPolicyId"] = value.pop("draw_policy_id")
        value["drawPolicyVersion"] = value.pop("draw_policy_version")
        value["randomAlgorithm"] = value.pop("random_algorithm")
        return value
