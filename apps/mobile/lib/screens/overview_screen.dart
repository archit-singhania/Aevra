import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';

/// Mobile counterpart of the web app's overview view — now wired to
/// [AppState] instead of static demo copy.
class OverviewScreen extends StatelessWidget {
  const OverviewScreen({super.key, required this.state});

  final AppState state;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: state,
      builder: (context, _) {
        final awaiting = state.campaigns.where((c) => c.status == 'awaiting_approval').length;
        final firstName = (state.user?.displayName ?? '').split(' ').firstOrNull ?? 'there';

        return RefreshIndicator(
          onRefresh: state.load,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
            children: [
              Text(
                'Good to see you, $firstName.',
                style: GoogleFonts.fraunces(
                  fontSize: 27,
                  fontWeight: FontWeight.w500,
                  letterSpacing: -0.015,
                  height: 1.1,
                  color: AevraColors.text,
                ),
              ),
              const SizedBox(height: 8),
              const Align(
                alignment: Alignment.centerRight,
                child: _AiOrb(),
              ),
              const Text(
                'Your Aevra control room is connected to the workspace.',
                style: TextStyle(fontSize: 13, height: 1.5, color: AevraColors.muted),
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(child: _stat('Brand Brain', '${state.documents.length}', 'indexed sources', AevraColors.lime)),
                  const SizedBox(width: 10),
                  Expanded(child: _stat('Campaigns', '${state.campaigns.length}', 'in workspace', AevraColors.violet)),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(child: _stat('Approval queue', '$awaiting', 'human decisions', AevraColors.cyan)),
                  const SizedBox(width: 10),
                  Expanded(child: _stat('Media assets', '${state.assets.length}', 'generated assets', AevraColors.lime)),
                ],
              ),
              const SizedBox(height: 14),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.auto_awesome_outlined, size: 16, color: AevraColors.lime),
                        SizedBox(width: 8),
                        Text('Recent campaigns', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                      ],
                    ),
                    if (state.loading && state.campaigns.isEmpty) ...[
                      const SizedBox(height: 16),
                      const Center(child: CircularProgressIndicator(strokeWidth: 2, color: AevraColors.lime)),
                    ] else if (state.campaigns.isEmpty) ...[
                      const SizedBox(height: 8),
                      const Text(
                        'Your campaign runway is clear. Create one from the Campaigns tab.',
                        style: TextStyle(fontSize: 11, color: AevraColors.muted2),
                      ),
                    ] else
                      for (final c in state.campaigns.take(4)) ...[
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                c.name,
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Text(
                              c.status.replaceAll('_', ' '),
                              style: const TextStyle(fontSize: 9, color: AevraColors.muted2),
                            ),
                          ],
                        ),
                      ],
                  ],
                ),
              ),
              if (state.error != null) ...[
                const SizedBox(height: 12),
                Text(state.error!, style: const TextStyle(fontSize: 11, color: Color(0xFFFFB4AA))),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _stat(String label, String value, String caption, Color color) {
    return GlassCard(
      borderColor: color.withOpacity(0.18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 10, color: AevraColors.muted2)),
          const SizedBox(height: 6),
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: double.tryParse(value) ?? 0),
            duration: const Duration(milliseconds: 720),
            curve: Curves.easeOutCubic,
            builder: (context, animated, _) => Text(
              value.contains('%') ? '${animated.round()}%' : animated.round().toString(),
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.w600, color: color),
            ),
          ),
          const SizedBox(height: 2),
          Text(caption, style: const TextStyle(fontSize: 9, color: AevraColors.muted2)),
        ],
      ),
    );
  }
}

class _AiOrb extends StatefulWidget {
  const _AiOrb();

  @override
  State<_AiOrb> createState() => _AiOrbState();
}

class _AiOrbState extends State<_AiOrb> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 2200),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) => Container(
        width: 42,
        height: 42,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AevraColors.lime.withOpacity(0.1 + _controller.value * 0.08),
          border: Border.all(color: AevraColors.lime.withOpacity(0.35)),
          boxShadow: [BoxShadow(color: AevraColors.lime.withOpacity(0.16), blurRadius: 20 + _controller.value * 8)],
        ),
        child: const Icon(Icons.auto_awesome, size: 18, color: AevraColors.lime),
      ),
    );
  }
}

extension _FirstOrNull<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
