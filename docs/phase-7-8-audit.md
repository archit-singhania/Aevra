# Phases 7–8 audit

Status: complete for the local, tenant-safe media foundation.

## Phase 7 — image pipeline

Built:

- Provider contract with deterministic offline rendering, stable request fingerprints, seeds,
  provenance metadata, output digests, and bounded dimensions/payloads.
- Pillow transforms for cover-crop, contain/letterbox, safe color parsing, logo compositing,
  brand overlays, and PNG/JPEG/WebP encoding.
- Campaign-scoped `media_assets` persistence with source/variant roles, parent lineage,
  platform metadata, dimensions, MIME type, byte size, SHA-256, and generation metadata.
- Tenant-authorized image endpoint that creates an original and platform-specific crops for
  LinkedIn, Instagram, Threads, X, Facebook, or YouTube.

Left:

- A GPU-backed FLUX-compatible provider adapter and object-storage/S3 adapter are configuration
  extensions; the default renderer is intentionally deterministic and works offline.
- Logo upload management and an admin visual-style editor are still product work.

## Phase 8 — video composer

Built:

- Validated image-slide composition contracts with slide, duration, FPS, color, canvas, file,
  and output-stem safety limits.
- Shell-free FFmpeg command construction with fixed filter values and path arguments, partial
  output promotion, timeout/error handling, and deterministic render keys/manifests.
- Required 9:16 (1080×1920), 1:1 (1080×1080), and 16:9 (1920×1080) canvases, plus a safe
  deterministic mock mode for machines without FFmpeg.
- Campaign video endpoint persists composition lineage and streams authorized MP4/manifest files.

Left:

- Motion templates, captions/subtitles, voiceover, music licensing, and multi-scene transitions
  are planned enhancements.
- Production deployments should use object storage and a background render queue rather than
  synchronous API rendering.

## Verification

- API suite: **52 passed**.
- Ruff: clean.
- Mypy: clean across 59 API source files.
- Migration `20260916_0005_media_assets.py` added and Docker API image now includes FFmpeg.
