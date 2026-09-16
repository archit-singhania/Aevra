import 'dart:ui' as ui;

import 'package:flutter/scheduler.dart';
import 'package:flutter/material.dart';

/// Full-bleed animated GPU background, driven by a hand-written GLSL
/// fragment shader (see shaders/background.frag) — the mobile counterpart
/// to the web app's WebGL background, same palette and motion language.
///
/// Falls back to a quiet static gradient if the shader fails to load (older
/// devices / engines without Impeller) or if the platform reports a
/// reduced-motion preference, in which case the animation simply stops on
/// its first frame instead of looping.
class ShaderBackground extends StatefulWidget {
  const ShaderBackground({super.key});

  @override
  State<ShaderBackground> createState() => _ShaderBackgroundState();
}

class _ShaderBackgroundState extends State<ShaderBackground> with SingleTickerProviderStateMixin {
  ui.FragmentShader? _shader;
  bool _failed = false;
  late final Ticker _ticker;
  double _time = 0;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_onTick);
    _load();
  }

  Future<void> _load() async {
    try {
      final program = await ui.FragmentProgram.fromAsset('shaders/background.frag');
      if (!mounted) return;
      setState(() => _shader = program.fragmentShader());
      _maybeStart();
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    }
  }

  void _maybeStart() {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    if (!reduceMotion) {
      _ticker.start();
    }
  }

  void _onTick(Duration elapsed) {
    setState(() => _time = elapsed.inMicroseconds / 1e6);
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_failed) return const _StaticFallback();
    final shader = _shader;
    if (shader == null) return const _StaticFallback();

    return IgnorePointer(
      child: CustomPaint(
        painter: _ShaderPainter(shader: shader, time: _time),
        size: Size.infinite,
      ),
    );
  }
}

class _ShaderPainter extends CustomPainter {
  _ShaderPainter({required this.shader, required this.time});

  final ui.FragmentShader shader;
  final double time;

  @override
  void paint(Canvas canvas, Size size) {
    shader
      ..setFloat(0, size.width)
      ..setFloat(1, size.height)
      ..setFloat(2, time);
    canvas.drawRect(Offset.zero & size, Paint()..shader = shader);
  }

  @override
  bool shouldRepaint(covariant _ShaderPainter oldDelegate) => oldDelegate.time != time;
}

class _StaticFallback extends StatelessWidget {
  const _StaticFallback();

  @override
  Widget build(BuildContext context) {
    return const DecoratedBox(
      decoration: BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(0.4, -0.6),
          radius: 1.2,
          colors: [Color(0x14B5FF5E), Color(0x00070911)],
        ),
      ),
    );
  }
}
