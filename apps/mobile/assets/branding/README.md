# Branding assets

Vector source of truth: `apps/web/public/brand/aevra-mark.svg`. The in-app mark
is drawn in code (`lib/widgets/aevra_logo.dart`) and needs no raster file — the
PNGs here exist only because the native launcher-icon and splash generators
cannot read SVG.

## Expected files

| File | Size | Alpha | Used by |
|---|---|---|---|
| `aevra_app_icon_1024.png` | 1024×1024 | **no** (iOS rejects alpha in app icons) | `flutter_launcher_icons` |
| `aevra_icon_foreground_1024.png` | 1024×1024 | yes | `flutter_launcher_icons` (Android adaptive icon foreground layer) |
| `aevra_splash_600.png` | 600×600 | yes | `flutter_native_splash` (iOS + Android ≤11) |
| `aevra_splash_android12_960.png` | 960×960 | yes | `flutter_native_splash` (Android 12+) |

The foreground asset exists because Android adaptive icons composite a
separate foreground layer over `adaptive_icon_background` (`#0A0B0D`, set in
`pubspec.yaml`) — the opaque square icon can't be reused here, since Android
crops that layer to a circle/squircle and would clip the mark.

The Android 12 asset is separate on purpose: that platform masks the splash
image to a circle and only the inner two-thirds is safe, so the mark is drawn
smaller on a larger canvas rather than being cropped.

## Generating them

They are rendered from the SVG above. Any rasterizer works; the reference
render is 64% mark on a `#0A0B0D` field for the icon, 42% transparent
(generous safe-zone padding) for the adaptive foreground, 55% transparent for
the standard splash, 38% transparent for the Android 12 one.

## Wiring them up

The mobile app currently ships **no `android/` or `ios/` folders**, so the
generators have nothing to write into. Create them once:

```bash
cd apps/mobile
flutter create --platforms=android,ios .
```

Then, with the four PNGs in this directory:

```bash
flutter pub get
dart run flutter_launcher_icons
dart run flutter_native_splash:create
```

Until the PNGs are present, both generators fail with a missing-file error —
but the app itself still builds and runs, because nothing in `lib/` references
them. The in-app boot screen in `main.dart` draws the vector mark directly and
covers the gap.
