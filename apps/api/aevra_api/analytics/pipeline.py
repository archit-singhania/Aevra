from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MetricSnapshot:
    platform: str
    external_post_id: str
    collected_at: datetime
    impressions: int
    engagements: int
    clicks: int
    likes: int
    comments: int
    shares: int

    @property
    def engagement_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return round((self.engagements / self.impressions) * 100, 4)


def normalize_metrics(
    platform: str,
    external_post_id: str,
    payload: dict[str, object],
    collected_at: datetime,
) -> MetricSnapshot:
    def non_negative(name: str) -> int:
        value = payload.get(name, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
        return value

    return MetricSnapshot(
        platform,
        external_post_id,
        collected_at,
        non_negative("impressions"),
        non_negative("engagements"),
        non_negative("clicks"),
        non_negative("likes"),
        non_negative("comments"),
        non_negative("shares"),
    )
