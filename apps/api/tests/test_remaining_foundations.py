from datetime import UTC, datetime

from aevra_api.analytics.pipeline import normalize_metrics
from aevra_api.media.storyboard import Scene, validate_music_license, webvtt
from aevra_api.publishing.uploads import DeterministicMediaUploader, MediaUploadRequest


def test_normalized_metrics_expose_safe_engagement_rate() -> None:
    metrics = normalize_metrics(
        "linkedin",
        "post-1",
        {"impressions": 1000, "engagements": 75, "clicks": 20, "likes": 40},
        datetime.now(UTC),
    )
    assert metrics.engagement_rate == 7.5


def test_free_media_upload_is_deterministic() -> None:
    result = DeterministicMediaUploader("instagram").upload(
        MediaUploadRequest("upload-1234", "account", b"image", "image/png", "hero.png"),
        access_token="opaque",
    )
    assert result.status == "ready"
    assert result.external_media_id.startswith("instagram_media_")


def test_storyboard_subtitles_and_music_license_are_bounded() -> None:
    scenes = (Scene(1, 2.0, "asset-1", "Hello"), Scene(2, 3.0, "asset-2", "World"))
    subtitles = webvtt(scenes)
    assert subtitles.startswith("WEBVTT")
    assert "00:00:02.000 --> 00:00:05.000" in subtitles
    validate_music_license({"license": "cc0"})
