from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scene:
    number: int
    duration_seconds: float
    image_asset_id: str
    caption: str = ""
    motion: str = "slow_zoom_in"


MOTION_PRESETS = frozenset(
    {"static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "fade"}
)


def validate_storyboard(scenes: tuple[Scene, ...]) -> tuple[Scene, ...]:
    if not scenes or len(scenes) > 24:
        raise ValueError("A storyboard must contain 1-24 scenes")
    for expected, scene in enumerate(scenes, start=1):
        if scene.number != expected or not 0.5 <= scene.duration_seconds <= 30:
            raise ValueError("scene order or duration is invalid")
        if scene.motion not in MOTION_PRESETS:
            raise ValueError("unsupported motion preset")
    return scenes


def webvtt(scenes: tuple[Scene, ...]) -> str:
    validate_storyboard(scenes)
    lines = ["WEBVTT", ""]
    cursor = 0.0
    for index, scene in enumerate(scenes, start=1):
        end = cursor + scene.duration_seconds
        lines.extend(
            [str(index), f"{_timestamp(cursor)} --> {_timestamp(end)}", scene.caption.strip(), ""]
        )
        cursor = end
    return "\n".join(lines)


def _timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f"00:{minutes:02d}:{remainder:06.3f}"


def validate_music_license(metadata: dict[str, object]) -> None:
    if metadata.get("license") not in {"owned", "cc0", "commercial", "user-uploaded"}:
        raise ValueError("music requires an explicit owned or compatible license")
