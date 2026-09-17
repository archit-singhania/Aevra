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
    platform: str, external_post_id: str, payload: dict[str, object], collected_at: datetime
) -> MetricSnapshot:
    def non_negative(name: str) -> int:
        value = payload.get(name, 0)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
        return value

    return MetricSnapshot(
        platform=platform,
        external_post_id=external_post_id,
        collected_at=collected_at,
        impressions=non_negative("impressions"),
        engagements=non_negative("engagements"),
        clicks=non_negative("clicks"),
        likes=non_negative("likes"),
        comments=non_negative("comments"),
        shares=non_negative("shares"),
    )
