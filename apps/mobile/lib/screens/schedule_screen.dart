import 'package:flutter/material.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';

class ScheduleScreen extends StatelessWidget {
  const ScheduleScreen({super.key});

  static const _days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  static const _posts = [
    (time: '09:30', title: 'Why developer tools fail quietly', meta: 'LinkedIn · Thought leadership', status: 'Review'),
    (time: '14:00', title: 'Inside the toolkit', meta: 'Instagram · Carousel', status: 'Ready'),
    (time: '17:30', title: 'Build faster, reason better', meta: 'YouTube · Short', status: 'Draft'),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        const Text('Schedule', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.02)),
        const SizedBox(height: 4),
        const Text('9 posts across 6 channels', style: TextStyle(fontSize: 12, color: AevraColors.muted2)),
        const SizedBox(height: 18),
        GlassCard(
          padding: const EdgeInsets.all(10),
          child: Row(
            children: List.generate(7, (i) {
              final today = i == 0;
              return Expanded(
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 2),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    color: today ? AevraColors.lime.withOpacity(0.08) : Colors.transparent,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    children: [
                      Text(_days[i], style: const TextStyle(fontSize: 9, color: AevraColors.muted2)),
                      const SizedBox(height: 4),
                      Text(
                        '${15 + i}',
                        style: TextStyle(
                          fontSize: 11,
                          fontFeatures: const [FontFeature.tabularFigures()],
                          color: today ? AevraColors.lime : AevraColors.muted,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
        const SizedBox(height: 14),
        for (final p in _posts) ...[
          GlassCard(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                SizedBox(
                  width: 44,
                  child: Text(p.time, style: const TextStyle(fontSize: 11, color: AevraColors.muted)),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(p.title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
                      const SizedBox(height: 2),
                      Text(p.meta, style: const TextStyle(fontSize: 9, color: AevraColors.muted2)),
                    ],
                  ),
                ),
                Text(p.status, style: const TextStyle(fontSize: 9, color: AevraColors.muted)),
              ],
            ),
          ),
          const SizedBox(height: 8),
        ],
      ],
    );
  }
}
