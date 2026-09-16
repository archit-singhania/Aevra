import json
import subprocess
from pathlib import Path

import pytest

from aevra_api.media.video_composer import (
    VideoComposer,
    build_ffmpeg_command,
    composition_render_key,
    validate_composition,
)
from aevra_api.media.video_contracts import (
    FFmpegExecutionError,
    FFmpegUnavailableError,
    VideoAspectRatio,
    VideoCompositionRequest,
    VideoSlide,
    VideoValidationError,
)


def make_image(tmp_path: Path, name: str, payload: bytes = b"synthetic-png-bytes") -> Path:
    image = tmp_path / name
    image.write_bytes(payload)
    return image


@pytest.mark.parametrize(
    ("aspect_ratio", "expected_canvas"),
    [
        (VideoAspectRatio.VERTICAL, {"width": 1080, "height": 1920}),
        (VideoAspectRatio.SQUARE, {"width": 1080, "height": 1080}),
        (VideoAspectRatio.LANDSCAPE, {"width": 1920, "height": 1080}),
    ],
)
def test_mock_renders_each_required_social_canvas(
    tmp_path: Path, aspect_ratio: VideoAspectRatio, expected_canvas: dict[str, int]
) -> None:
    image = make_image(tmp_path, "asset.png")
    request = VideoCompositionRequest(
        slides=(VideoSlide(image, 2.5),),
        aspect_ratio=aspect_ratio,
        fps=30,
        output_stem="launch-cut",
    )

    result = VideoComposer(tmp_path / "renders", execution_mode="mock").compose(request)

    assert result.mode == "deterministic_mock"
    assert result.output_path.suffixes == [".render", ".json"]
    assert result.canvas.width == expected_canvas["width"]
    assert result.canvas.height == expected_canvas["height"]
    assert result.frame_count == 75
    persisted = json.loads(result.output_path.read_text(encoding="utf-8"))
    assert persisted["canvas"] == expected_canvas
    assert persisted["aspect_ratio"] == aspect_ratio.value
    assert persisted["mode"] == "deterministic_mock"


def test_mock_render_is_repeatable_and_does_not_leak_source_paths(tmp_path: Path) -> None:
    source = make_image(tmp_path, "confidential asset.png", b"same-image-content")
    request = VideoCompositionRequest(
        slides=(VideoSlide(source, 3.0),),
        aspect_ratio=VideoAspectRatio.VERTICAL,
        output_stem="campaign",
    )
    composer = VideoComposer(tmp_path / "renders", execution_mode="mock")

    first = composer.compose(request)
    second = composer.compose(request)

    assert (
        first.render_key
        == second.render_key
        == composition_render_key(validate_composition(request))
    )
    assert first.output_path == second.output_path
    assert first.output_path.read_bytes() == second.output_path.read_bytes()
    assert str(source.resolve()) not in first.output_path.read_text(encoding="utf-8")


def test_ffmpeg_command_uses_fixed_filter_values_and_argument_paths(tmp_path: Path) -> None:
    hostile_name = "asset;touch-not-executed.png"
    source = make_image(tmp_path, hostile_name)
    request = VideoCompositionRequest(
        slides=(VideoSlide(source, 2.0), VideoSlide(source, 3.0)),
        aspect_ratio=VideoAspectRatio.LANDSCAPE,
        fps=24,
        background_color="#102030",
    )
    composition = validate_composition(request)
    output = tmp_path / "output.mp4"

    command = build_ffmpeg_command(composition, output_path=output, ffmpeg_binary="ffmpeg")
    filter_graph = command[command.index("-filter_complex") + 1]

    assert command[:5] == ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin"]
    assert command.count(str(source.resolve())) == 2
    assert hostile_name not in filter_graph
    assert "scale=1920:1080:force_original_aspect_ratio=decrease" in filter_graph
    assert "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x102030" in filter_graph
    assert "fps=24" in filter_graph
    assert "setsar=1" in filter_graph
    assert command[-1] == str(output.resolve())
    assert "-y" in command
    assert "-an" in command
    assert "+faststart" in command


def test_auto_uses_mock_when_ffmpeg_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = make_image(tmp_path, "asset.png")
    composer = VideoComposer(tmp_path / "renders", execution_mode="auto")
    monkeypatch.setattr(composer, "_ffmpeg_is_available", lambda: False)

    result = composer.compose(VideoCompositionRequest(slides=(VideoSlide(source),)))

    assert result.mode == "deterministic_mock"


def test_explicit_ffmpeg_mode_fails_cleanly_when_binary_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = make_image(tmp_path, "asset.png")
    composer = VideoComposer(tmp_path / "renders", execution_mode="ffmpeg")
    monkeypatch.setattr(composer, "_ffmpeg_is_available", lambda: False)

    with pytest.raises(FFmpegUnavailableError, match="was not found"):
        composer.compose(VideoCompositionRequest(slides=(VideoSlide(source),)))


def test_ffmpeg_mode_runs_without_a_shell_and_promotes_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = make_image(tmp_path, "asset.png")
    composer = VideoComposer(tmp_path / "renders", execution_mode="ffmpeg")
    monkeypatch.setattr(composer, "_ffmpeg_is_available", lambda: True)
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["kwargs"] = kwargs
        Path(command[-1]).write_bytes(b"mp4-placeholder")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("aevra_api.media.video_composer.subprocess.run", fake_run)

    result = composer.compose(
        VideoCompositionRequest(slides=(VideoSlide(source, 1.0),), output_stem="safe-output")
    )

    assert result.mode == "ffmpeg"
    assert result.output_path.suffix == ".mp4"
    assert result.output_path.read_bytes() == b"mp4-placeholder"
    assert result.ffmpeg_command == tuple(captured["command"])  # type: ignore[arg-type]
    kwargs = captured["kwargs"]
    assert kwargs["shell"] is False
    assert kwargs["check"] is True
    assert kwargs["timeout"] == 240.0
    assert ".partial.mp4" not in result.output_path.name


def test_ffmpeg_empty_output_is_a_safe_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = make_image(tmp_path, "asset.png")
    composer = VideoComposer(tmp_path / "renders", execution_mode="ffmpeg")
    monkeypatch.setattr(composer, "_ffmpeg_is_available", lambda: True)

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        Path(command[-1]).touch()
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("aevra_api.media.video_composer.subprocess.run", fake_run)

    with pytest.raises(FFmpegExecutionError, match="without producing"):
        composer.compose(VideoCompositionRequest(slides=(VideoSlide(source),)))


@pytest.mark.parametrize(
    "invalid_request",
    [
        VideoCompositionRequest(slides=()),
        VideoCompositionRequest(slides=(VideoSlide("missing.png"),)),
        VideoCompositionRequest(slides=(VideoSlide("source.txt"),)),
        VideoCompositionRequest(slides=(VideoSlide("source.png", 0.1),)),
        VideoCompositionRequest(slides=(VideoSlide("source.png"),), fps=61),
        VideoCompositionRequest(slides=(VideoSlide("source.png"),), background_color="blue"),
        VideoCompositionRequest(slides=(VideoSlide("source.png"),), output_stem="../escape"),
    ],
)
def test_invalid_composition_is_rejected_before_command_construction(
    tmp_path: Path, invalid_request: VideoCompositionRequest
) -> None:
    source = make_image(tmp_path, "source.png")
    adjusted_request = invalid_request
    if invalid_request.slides and invalid_request.slides[0].source_path == "source.png":
        adjusted_request = VideoCompositionRequest(
            slides=(VideoSlide(source, invalid_request.slides[0].duration_seconds),),
            aspect_ratio=invalid_request.aspect_ratio,
            fps=invalid_request.fps,
            background_color=invalid_request.background_color,
            output_stem=invalid_request.output_stem,
        )

    with pytest.raises(VideoValidationError):
        validate_composition(adjusted_request)
