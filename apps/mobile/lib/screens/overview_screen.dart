import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
import '../widgets/advanced_ui.dart';
import '../widgets/depth.dart';
import '../widgets/glass_card.dart';

/// Mobile counterpart of the web app's overview view.
class OverviewScreen extends StatefulWidget {
  const OverviewScreen({super.key, required this.state});

  final AppState state;

  @override
  State<OverviewScreen> createState() => _OverviewScreenState();
}

/// One tile of the bento grid. Values are resolved at build time from
/// [AppState], so reordering only moves the definition, never the data.
class _StatSpec {
  const _StatSpec(this.id, this.label, this.caption, this.icon, this.color, this.read);

  final String id;
  final String label;
  final String caption;
  final IconData icon;
  final Color color;
  final int Function(AppState) read;
}

class _OverviewScreenState extends State<OverviewScreen> {
  static final List<_StatSpec> _specs = [
    _StatSpec('brain', 'Brand Brain', 'indexed sources', Icons.hub_outlined, AevraColors.lime,
        (s) => s.documents.length),
    _StatSpec('campaigns', 'Campaigns', 'in workspace', Icons.auto_awesome_outlined, AevraColors.violet,
        (s) => s.campaigns.length),
    _StatSpec('queue', 'Approval queue', 'human decisions', Icons.how_to_reg_outlined, AevraColors.cyan,
        (s) => s.campaigns.where((c) => c.status == 'awaiting_approval').length),
    _StatSpec('media', 'Media assets', 'generated assets', Icons.image_outlined, AevraColors.lime,
        (s) => s.assets.length),
  ];

  /// #10 — persisted bento order (indexes into [_specs]).
  List<int> _order = List<int>.generate(_specs.length, (i) => i);

  @override
  void initState() {
    super.initState();
    loadBentoOrder(_specs.length).then((saved) {
      if (saved != null && mounted) setState(() => _order = saved);
    });
  }

  void _reorder(int oldIndex, int newIndex) {
    HapticFeedback.mediumImpact();
    setState(() {
      if (newIndex > oldIndex) newIndex -= 1;
      final moved = _order.removeAt(oldIndex);
      _order.insert(newIndex, moved);
    });
    saveBentoOrder(_order);
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    return AnimatedBuilder(
      animation: state,
      builder: (context, _) {
        final firstName = (state.user?.displayName ?? '').split(' ').firstOrNull ?? 'there';
        final firstLoad = state.loading && state.campaigns.isEmpty && state.documents.isEmpty;

        // #18 — adaptive glass: every GlassCard below reads scroll intensity
        // from this scope and densifies as the user scrolls.
        return AdaptiveGlassScroll(
          child: RefreshIndicator(
            onRefresh: state.load,
            color: AevraColors.lime,
            backgroundColor: AevraColors.panel,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                ParallaxLayer(
                  depth: -1.6,
                  child: Reveal(
                    index: 0,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Text(
                            'Good to see you, $firstName.',
                            style: GoogleFonts.fraunces(
                              fontSize: 30,
                              fontWeight: FontWeight.w500,
                              letterSpacing: -0.02,
                              height: 1.05,
                              color: AevraColors.text,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        // #6 — shared orb, now state-aware.
                        AiOrb(state: state.loading ? AiOrbState.thinking : AiOrbState.idle),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                ParallaxLayer(
                  depth: -1.1,
                  child: const Reveal(
                    index: 1,
                    child: Text(
                      'Your Aevra control room is connected to the workspace.',
                      style: TextStyle(fontSize: 13, height: 1.5, color: AevraColors.muted),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                if (firstLoad)
                  // #4 — skeleton shimmer instead of a bare spinner.
                  Column(
                    children: List.generate(
                      2,
                      (i) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: Row(
                          children: const [
                            Expanded(child: GlassCard(child: ShimmerStatCard())),
                            SizedBox(width: 10),
                            Expanded(child: GlassCard(child: ShimmerStatCard())),
                          ],
                        ),
                      ),
                    ),
                  )
                else
                  _bento(state),
                const SizedBox(height: 14),
                Reveal(
                  index: 6,
                  child: GlassSurface(
                    elevation: GlassElevation.floating,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: const [
                            Icon(Icons.auto_awesome_outlined, size: 16, color: AevraColors.lime),
                            SizedBox(width: 8),
                            Text('Recent campaigns',
                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                          ],
                        ),
                        if (firstLoad) ...[
                          const SizedBox(height: 12),
                          const ShimmerList(count: 3),
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
                ),
                if (state.error != null) ...[
                  const SizedBox(height: 12),
                  Text(state.error!, style: const TextStyle(fontSize: 11, color: Color(0xFFFFB4AA))),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  /// #10 — long-press any tile to drag it; the order persists across launches.
  Widget _bento(AppState state) {
    return ReorderableListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      buildDefaultDragHandles: false,
      padding: EdgeInsets.zero,
      itemCount: _order.length,
      onReorder: _reorder,
      proxyDecorator: (child, index, animation) => Material(
        color: Colors.transparent,
        child: Transform.scale(scale: 1.03, child: child),
      ),
      itemBuilder: (context, position) {
        final spec = _specs[_order[position]];
        return ReorderableDelayedDragStartListener(
          key: ValueKey(spec.id),
          index: position,
          child: Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Reveal(index: 2 + position, child: _tile(spec, spec.read(state))),
          ),
        );
      },
    );
  }

  Widget _tile(_StatSpec spec, int value) {
    // Tilt is tap-driven only (enablePan stays false): these tiles also host
    // ReorderableListView's long-press drag, and a pan-tilt would contend
    // with it in the gesture arena.
    return DepthCard(
      elevation: GlassElevation.floating,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: spec.color.withOpacity(0.10),
              border: Border.all(color: spec.color.withOpacity(0.22)),
            ),
            child: Icon(spec.icon, size: 17, color: spec.color),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(spec.label,
                    style: const TextStyle(
                        fontSize: 11, fontWeight: FontWeight.w500, color: AevraColors.muted)),
                const SizedBox(height: 2),
                Text(spec.caption, style: const TextStyle(fontSize: 9, color: AevraColors.muted2)),
              ],
            ),
          ),
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: value.toDouble()),
            duration: const Duration(milliseconds: 720),
            curve: Curves.easeOutCubic,
            builder: (context, animated, _) => Text(
              animated.round().toString(),
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w600,
                color: spec.color,
                letterSpacing: -0.02,
              ),
            ),
          ),
          const SizedBox(width: 10),
          const Icon(Icons.drag_indicator_rounded, size: 16, color: AevraColors.muted2),
        ],
      ),
    );
  }
}

extension _FirstOrNull<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
