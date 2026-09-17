import 'dart:ui';

import 'package:flutter/material.dart';
import '../theme/aevra_theme.dart';

/// The mobile counterpart of the web app's `.panel` — a translucent,
/// blurred glass surface that lets the animated shader background show
/// through, with a hairline border and soft inner highlight.
class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.borderColor,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: AevraColors.panel.withOpacity(0.6),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: borderColor ?? AevraColors.line),
          ),
          child: child,
        ),
      ),
    );
  }
}

/// A small circular progress ring used for scores (mirrors `.score-ring`).
class ScoreRing extends StatelessWidget {
  const ScoreRing({super.key, required this.value, this.label = '/100', this.color = AevraColors.cyan});

  final int value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 66,
      height: 66,
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 66,
            height: 66,
            child: CircularProgressIndicator(
              value: value / 100,
              strokeWidth: 4,
              backgroundColor: const Color(0xFF252B34),
              valueColor: AlwaysStoppedAnimation(color),
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '$value',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Colors.white),
              ),
              Text(label, style: const TextStyle(fontSize: 8, color: AevraColors.muted2)),
            ],
          ),
        ],
      ),
    );
  }
}
