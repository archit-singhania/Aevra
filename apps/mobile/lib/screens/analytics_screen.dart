import 'package:flutter/material.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';

class AnalyticsScreen extends StatelessWidget {
  const AnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        const Text('Analytics', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.02)),
        const SizedBox(height: 4),
        const Text('Last 30 days', style: TextStyle(fontSize: 12, color: AevraColors.muted2)),
        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(child: _stat('Engagement', '7.5%', AevraColors.lime)),
            const SizedBox(width: 10),
            Expanded(child: _stat('Reach', '48.2k', AevraColors.violet)),
          ],
        ),
        const SizedBox(height: 10),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Row(
                children: [
                  Icon(Icons.insights_outlined, size: 16, color: AevraColors.cyan),
                  SizedBox(width: 8),
                  Text('LinkedIn is leading', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                ],
              ),
              SizedBox(height: 4),
              Text('Highest completion rate across connected channels', style: TextStyle(fontSize: 10, color: AevraColors.muted2)),
            ],
          ),
        ),
        const SizedBox(height: 10),
        GlassCard(
          child: Row(
            children: const [
              Icon(Icons.check_circle_outline, size: 16, color: AevraColors.lime),
              SizedBox(width: 8),
              Expanded(child: Text('Metrics synced today', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500))),
            ],
          ),
        ),
      ],
    );
  }

  Widget _stat(String label, String value, Color color) {
    return GlassCard(
      borderColor: color.withOpacity(0.18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, color: color)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(fontSize: 10, color: AevraColors.muted2)),
        ],
      ),
    );
  }
}
