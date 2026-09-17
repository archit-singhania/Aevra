import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
import '../widgets/advanced_ui.dart';
import '../widgets/depth.dart';
import '../widgets/glass_card.dart';

class ScheduleScreen extends StatelessWidget {
  const ScheduleScreen({super.key, required this.state});

  final AppState state;

  String _formatTime(String iso) {
    final dt = DateTime.tryParse(iso);
    if (dt == null) return '—';
    final local = dt.toLocal();
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }

  String _formatDay(String iso) {
    final dt = DateTime.tryParse(iso);
    if (dt == null) return '';
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dt.weekday - 1];
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: state,
      builder: (context, _) {
        final scheduled = state.scheduled;
        return AdaptiveGlassScroll(
          child: RefreshIndicator(
          onRefresh: state.load,
          color: AevraColors.lime,
          backgroundColor: AevraColors.panel,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
            children: [
              ParallaxLayer(
                depth: -1.4,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Schedule', style: GoogleFonts.fraunces(fontSize: 28, fontWeight: FontWeight.w500, letterSpacing: -0.02, color: AevraColors.text)),
                          const SizedBox(height: 4),
                          Text('${scheduled.length} scheduled posts', style: const TextStyle(fontSize: 12, color: AevraColors.muted2)),
                        ],
                      ),
                    ),
                    AiOrb(size: 32, state: state.loading ? AiOrbState.thinking : AiOrbState.idle),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              if (state.loading && scheduled.isEmpty)
                const GlassCard(child: ShimmerList(count: 4))
              else if (scheduled.isEmpty)
                const Text(
                  'No scheduled posts. Approved content can be scheduled from the web app.',
                  style: TextStyle(fontSize: 12, color: AevraColors.muted2),
                )
              else
                for (final (i, p) in scheduled.indexed) ...[
                  Reveal(
                    index: i,
                    child: DepthCard(
                    elevation: GlassElevation.raised,
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        SizedBox(
                          width: 52,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(_formatTime(p.scheduledFor), style: const TextStyle(fontSize: 11, color: AevraColors.text)),
                              Text(_formatDay(p.scheduledFor), style: const TextStyle(fontSize: 9, color: AevraColors.muted2)),
                            ],
                          ),
                        ),
                        Expanded(
                          child: Text(
                            p.text?.isNotEmpty == true ? p.text! : 'Campaign post',
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Text(
                          p.status.replaceAll('_', ' '),
                          style: const TextStyle(fontSize: 9, color: AevraColors.muted),
                        ),
                      ],
                    ),
                  ),
                  ),
                  const SizedBox(height: 8),
                ],
            ],
          ),
          ),
        );
      },
    );
  }
}
