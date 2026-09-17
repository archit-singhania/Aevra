import 'package:flutter/material.dart';

import '../theme/aevra_theme.dart';

/// The Aevra brand mark — a vector-drawn monogram, not an image asset, so it
/// stays crisp at any size and always tracks the live theme tokens.
///
/// Geometry: a rounded square (radius mismatched on one corner, matching the
/// web app's `.live-logo span` — 8px/8px/8px/2px) rotated -32°, containing a
/// minimal apex-and-crossbar "A" ligature traced in the brass accent. This
/// mirrors the sidebar brand mark on web (`.brand-mark`) so both platforms
/// share one identity instead of two different placeholder glyphs.
class AevraMark extends StatelessWidget {
  const AevraMark({super.key, this.size = 26, this.color});

  final double size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _AevraMarkPainter(color: color ?? AevraColors.lime)),
    );
  }
}

class _AevraMarkPainter extends CustomPainter {
  _AevraMarkPainter({required this.color});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = size.width * 0.078;
    final rrPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..color = color.withOpacity(0.9)
      ..strokeCap = StrokeCap.round;

    canvas.save();
    canvas.translate(size.width / 2, size.height / 2);
    canvas.rotate(-32 * 3.14159265 / 180);
    canvas.translate(-size.width / 2, -size.height / 2);

    final rect = Rect.fromLTWH(
      size.width * 0.12,
      size.height * 0.12,
      size.width * 0.76,
      size.height * 0.76,
    );
    final rr = RRect.fromRectAndCorners(
      rect,
      topLeft: Radius.circular(size.width * 0.22),
      topRight: Radius.circular(size.width * 0.22),
      bottomRight: Radius.circular(size.width * 0.34),
      bottomLeft: Radius.circular(size.width * 0.06),
    );
    canvas.drawRRect(rr, rrPaint);
    canvas.restore();

    // Apex-and-crossbar "A" ligature, drawn axis-aligned (not rotated with
    // the frame) so the monogram itself always reads upright.
    final markPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke * 0.86
      ..strokeCap = StrokeCap.round
      ..color = color;
    final cx = size.width / 2;
    final top = Offset(cx, size.height * 0.28);
    final left = Offset(size.width * 0.32, size.height * 0.72);
    final right = Offset(size.width * 0.68, size.height * 0.72);
    canvas.drawLine(top, left, markPaint);
    canvas.drawLine(top, right, markPaint);
    canvas.drawLine(
      Offset(size.width * 0.40, size.height * 0.55),
      Offset(size.width * 0.60, size.height * 0.55),
      markPaint..strokeWidth = stroke * 0.6,
    );
  }

  @override
  bool shouldRepaint(covariant _AevraMarkPainter oldDelegate) => oldDelegate.color != color;
}

/// Mark + wordmark, matching the web app's `.live-logo` / `.brand-row`
/// composition. Use in top bars and the auth screen.
class AevraWordmark extends StatelessWidget {
  const AevraWordmark({super.key, this.markSize = 26, this.fontSize = 17, this.color});

  final double markSize;
  final double fontSize;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        AevraMark(size: markSize, color: color),
        const SizedBox(width: 10),
        Text(
          'AEVRA',
          style: TextStyle(
            fontSize: fontSize,
            fontWeight: FontWeight.w700,
            letterSpacing: 3,
            color: color ?? AevraColors.text,
          ),
        ),
      ],
    );
  }
}
