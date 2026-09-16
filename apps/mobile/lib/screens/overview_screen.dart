import 'package:flutter/material.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';

class OverviewScreen extends StatelessWidget {
  const OverviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        const Text(
          'Your brand, in motion.',
          style: TextStyle(fontSize: 30, fontWeight: FontWeight.w600, letterSpacing: -0.03, height: 1.05),
        ),
        const SizedBox(height: 8),
        const Text(
          'Shape the next campaign. Aevra keeps every idea grounded, adapted, and ready for approval.',
          style: TextStyle(fontSize: 13, height: 1.5, color: AevraColors.muted),
        ),
        const SizedBox(height: 20),
        GlassCard(
          borderColor: AevraColors.lime.withOpacity(0.18),
          child: Row(
            children: [
              const ScoreRing(value: 94, color: AevraColors.cyan),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Excellent alignment', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    const Text('Up 7 points this month', style: TextStyle(fontSize: 11, color: AevraColors.muted2)),
                    const SizedBox(height: 10),
                    _meter('Voice consistency', 0.96),
                    _meter('Claim grounding', 0.93),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Row(
                children: [
                  Icon(Icons.auto_awesome_outlined, size: 16, color: AevraColors.lime),
                  SizedBox(width: 8),
                  Text('Active campaigns', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                ],
              ),
              SizedBox(height: 4),
              Text('3 active · 12 approved variants', style: TextStyle(fontSize: 11, color: AevraColors.muted2)),
            ],
          ),
        ),
        const SizedBox(height: 12),
        GlassCard(
          child: Row(
            children: const [
              Icon(Icons.podcasts_outlined, size: 16, color: AevraColors.violet),
              SizedBox(width: 8),
              Expanded(
                child: Text('6 connected channels', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _meter(String label, double value) {
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontSize: 9, color: AevraColors.muted2)),
              Text('${(value * 100).round()}%', style: const TextStyle(fontSize: 9, color: AevraColors.muted)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: value,
              minHeight: 3,
              backgroundColor: const Color(0xFF222832),
              valueColor: const AlwaysStoppedAnimation(AevraColors.cyan),
            ),
          ),
        ],
      ),
    );
  }
}
