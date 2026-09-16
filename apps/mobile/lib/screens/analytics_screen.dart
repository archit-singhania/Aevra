import 'package:flutter/material.dart';
import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';

class AnalyticsScreen extends StatelessWidget {
  const AnalyticsScreen({super.key, required this.state});

  final AppState state;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: state,
      builder: (context, _) {
        final campaigns = state.campaigns;
        final approved = campaigns.where((c) => c.status == 'approved' || c.status == 'published').length;
        final approvalRate = campaigns.isEmpty ? 0 : ((approved / campaigns.length) * 100).round();
        final connected = state.accounts.where((a) => a.status == 'connected').length;

        return RefreshIndicator(
          onRefresh: state.load,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
            children: [
              const Text('Analytics', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: -0.02)),
              const SizedBox(height: 4),
              const Text('This workspace', style: TextStyle(fontSize: 12, color: AevraColors.muted2)),
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(child: _stat('Approval rate', '$approvalRate%', AevraColors.lime)),
                  const SizedBox(width: 10),
                  Expanded(child: _stat('Connected accounts', '$connected', AevraColors.violet)),
                ],
              ),
              const SizedBox(height: 10),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.insights_outlined, size: 16, color: AevraColors.cyan),
                        SizedBox(width: 8),
                        Text('Campaign mix', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${state.campaigns.length} campaigns · ${state.assets.length} media assets · '
                      '${state.documents.length} indexed sources',
                      style: const TextStyle(fontSize: 10, color: AevraColors.muted2, height: 1.5),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              GlassCard(
                child: _AnimatedBars(
                  values: [
                    campaigns.length.toDouble(),
                    approved.toDouble(),
                    state.assets.length.toDouble(),
                    state.documents.length.toDouble(),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              GlassCard(
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_outline, size: 16, color: AevraColors.lime),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        state.loading ? 'Syncing workspace…' : 'Synced with the live workspace',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
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

class _AnimatedBars extends StatelessWidget {
  const _AnimatedBars({required this.values});

  final List<double> values;

  @override
  Widget build(BuildContext context) {
    final maxValue = values.fold<double>(1, (max, value) => value > max ? value : max);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(Icons.bar_chart_rounded, size: 16, color: AevraColors.violet),
            SizedBox(width: 8),
            Text('Signal activity', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 14),
        SizedBox(
          height: 72,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: values.map((value) {
              return TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: value / maxValue),
                duration: const Duration(milliseconds: 800),
                curve: Curves.easeOutCubic,
                builder: (context, progress, _) => Container(
                  width: 26,
                  height: 64 * progress + 4,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    gradient: const LinearGradient(
                      begin: Alignment.bottomCenter,
                      end: Alignment.topCenter,
                      colors: [AevraColors.violet, AevraColors.cyan],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 8),
        const Text('campaigns · approved · media · sources', style: TextStyle(fontSize: 9, color: AevraColors.muted2)),
      ],
    );
  }
}
