import 'package:flutter/material.dart';
import '../theme/aevra_theme.dart';
import 'depth.dart';

/// The mobile counterpart of the web app's `.panel`.
///
/// This is now a thin alias over [GlassSurface] at the `raised` tier. Keeping
/// the old name means the four screens didn't need touching, but there is
/// only one frosted-surface implementation in the app rather than two that
/// drift apart.
class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.borderColor,
    this.elevation = GlassElevation.raised,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? borderColor;
  final GlassElevation elevation;

  @override
  Widget build(BuildContext context) {
    return GlassSurface(
      elevation: elevation,
      padding: padding,
      borderColor: borderColor,
      child: child,
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
