import 'package:flutter/material.dart';
import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
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
        return RefreshIndicator(
          onRefresh: state.load,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
            children: [
              const Text('Schedule', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.02)),
              const SizedBox(height: 4),
              Text('${scheduled.length} scheduled posts', style: const TextStyle(fontSize: 12, color: AevraColors.muted2)),
              const SizedBox(height: 18),
              if (state.loading && scheduled.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 24),
                  child: Center(child: CircularProgressIndicator(strokeWidth: 2, color: AevraColors.lime)),
                )
              else if (scheduled.isEmpty)
                const Text(
                  'No scheduled posts. Approved content can be scheduled from the web app.',
                  style: TextStyle(fontSize: 12, color: AevraColors.muted2),
                )
              else
                for (final p in scheduled) ...[
                  GlassCard(
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
                  const SizedBox(height: 8),
                ],
            ],
          ),
        );
      },
    );
  }
}
