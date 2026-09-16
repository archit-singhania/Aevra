import 'package:flutter/material.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';

class CampaignsScreen extends StatelessWidget {
  const CampaignsScreen({super.key});

  static const _campaigns = [
    (title: 'Launch campaign', status: 'Ready', color: AevraColors.lime, platform: 'LinkedIn · YouTube'),
    (title: 'Product education', status: 'Review', color: Color(0xFFE1C66E), platform: 'Instagram'),
    (title: 'Community stories', status: 'Draft', color: AevraColors.muted, platform: 'Threads'),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        const Text('Campaigns', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.02)),
        const SizedBox(height: 4),
        const Text('8 in this workspace', style: TextStyle(fontSize: 12, color: AevraColors.muted2)),
        const SizedBox(height: 18),
        for (final c in _campaigns) ...[
          GlassCard(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(c.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 3),
                      Text(c.platform, style: const TextStyle(fontSize: 10, color: AevraColors.muted2)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: c.color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: c.color.withOpacity(0.3)),
                  ),
                  child: Text(c.status, style: TextStyle(fontSize: 9, color: c.color)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
        ],
      ],
    );
  }
}
