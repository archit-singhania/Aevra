import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../api/models.dart';
import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
import '../widgets/advanced_ui.dart';
import '../widgets/depth.dart';
import '../widgets/glass_card.dart';

class CampaignsScreen extends StatelessWidget {
  const CampaignsScreen({super.key, required this.state});

  final AppState state;

  Color _statusColor(String status) {
    switch (status) {
      case 'approved':
      case 'ready':
      case 'published':
        return AevraColors.lime;
      case 'awaiting_approval':
        return const Color(0xFFE1C66E);
      case 'failed':
      case 'rejected':
        return const Color(0xFFFFAAA0);
      default:
        return AevraColors.muted;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: state,
      builder: (context, _) {
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
                          Text('Campaigns', style: GoogleFonts.fraunces(fontSize: 28, fontWeight: FontWeight.w500, letterSpacing: -0.02, color: AevraColors.text)),
                          const SizedBox(height: 4),
                          Text('${state.campaigns.length} in this workspace', style: const TextStyle(fontSize: 12, color: AevraColors.muted2)),
                        ],
                      ),
                    ),
                    // #6 — orb spins while a decision or refresh is in flight.
                    AiOrb(size: 32, state: state.loading ? AiOrbState.thinking : AiOrbState.idle),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              if (state.loading && state.campaigns.isEmpty)
                // #4 — skeleton shimmer in place of the bare spinner.
                const GlassCard(child: ShimmerList(count: 4))
              else if (state.campaigns.isEmpty)
                const Text(
                  'No campaigns yet. Create one from the web app to see it here.',
                  style: TextStyle(fontSize: 12, color: AevraColors.muted2),
                )
              else
                for (final (i, c) in state.campaigns.indexed) ...[
                  Reveal(
                    index: i,
                    child: Dismissible(
                    key: ValueKey(c.id),
                    direction: c.status == 'awaiting_approval'
                        ? DismissDirection.horizontal
                        : DismissDirection.none,
                    background: _swipeBackground(alignLeft: true, approve: true),
                    secondaryBackground: _swipeBackground(alignLeft: false, approve: false),
                    confirmDismiss: (direction) async {
                      HapticFeedback.mediumImpact();
                      final decision = direction == DismissDirection.startToEnd ? 'approve' : 'reject';
                      await state.decide(c.id, decision);
                      // #3 + #16 — brass particle burst and ambient chime on
                      // a human decision, same trigger points as web.
                      if (context.mounted) AevraServices.celebrate(context);
                      return false; // let the card animate back; the list re-renders from state
                    },
                    // Tap is handled by the DepthCard below so the press
                    // also drives the tilt; an outer GestureDetector here
                    // would open the sheet twice.
                    child: Hero(
                        tag: 'campaign-${c.id}',
                        flightShuttleBuilder: (_, animation, __, ___, ____) =>
                            Material(color: Colors.transparent, child: FadeTransition(opacity: animation, child: _cardFor(c))),
                        child: DepthCard(
                          elevation: GlassElevation.floating,
                          padding: const EdgeInsets.all(16),
                          onTap: () {
                            HapticFeedback.selectionClick();
                            _openDetail(context, c);
                          },
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(c.name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                                    const SizedBox(height: 3),
                                    Text(
                                      c.platforms.join(' · '),
                                      style: const TextStyle(fontSize: 10, color: AevraColors.muted2),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: _statusColor(c.status).withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(color: _statusColor(c.status).withOpacity(0.3)),
                                ),
                                child: Text(
                                  c.status.replaceAll('_', ' '),
                                  style: TextStyle(fontSize: 9, color: _statusColor(c.status)),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ),
                  ),
                  const SizedBox(height: 10),
                ],
            ],
          ),
          ),
        );
      },
    );
  }

  Widget _cardFor(Campaign c) => GlassCard(
        padding: const EdgeInsets.all(16),
        child: Text(c.name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
      );

  Widget _swipeBackground({required bool alignLeft, required bool approve}) {
    return Container(
      alignment: alignLeft ? Alignment.centerLeft : Alignment.centerRight,
      padding: const EdgeInsets.symmetric(horizontal: 22),
      decoration: BoxDecoration(
        color: (approve ? AevraColors.lime : const Color(0xFFFFAAA0)).withOpacity(0.14),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Icon(
        approve ? Icons.check_circle_outline : Icons.close,
        color: approve ? AevraColors.lime : const Color(0xFFFFAAA0),
      ),
    );
  }

  Future<void> _openDetail(BuildContext context, Campaign campaign) async {
    final token = state.token;
    final workspace = state.workspace;
    if (token == null || workspace == null) return;
    List<ContentVariant> variants = [];
    try {
      variants = await state.client.variants(token, workspace.id, campaign.id);
    } catch (_) {
      // Leave variants empty; the sheet still shows the campaign status.
    }
    if (!context.mounted) return;
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => _CampaignDetailSheet(state: state, campaign: campaign, variants: variants),
    );
  }
}

class _CampaignDetailSheet extends StatelessWidget {
  const _CampaignDetailSheet({required this.state, required this.campaign, required this.variants});

  final AppState state;
  final Campaign campaign;
  final List<ContentVariant> variants;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        margin: const EdgeInsets.all(12),
        constraints: const BoxConstraints(maxHeight: 560),
        child: GlassSurface(
          elevation: GlassElevation.lifted,
          radius: 20,
          padding: const EdgeInsets.all(18),
          adaptive: false,
          borderColor: AevraColors.lineStrong,
          child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Hero(
              tag: 'campaign-${campaign.id}',
              child: Material(
                color: Colors.transparent,
                child: Text(campaign.name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              campaign.status.replaceAll('_', ' '),
              style: const TextStyle(fontSize: 11, color: AevraColors.muted2),
            ),
            const SizedBox(height: 14),
            Flexible(
              child: variants.isEmpty
                  ? const Text('No generated variants yet.', style: TextStyle(fontSize: 12, color: AevraColors.muted2))
                  : ListView.separated(
                      // #7 — variants stagger in as the sheet opens.
                      shrinkWrap: true,
                      itemCount: variants.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (context, i) {
                        final v = variants[i];
                        return Reveal(
                          index: i,
                          // Deliberately a plain Container, not a GlassCard:
                          // this sits inside the lifted glass sheet, and a
                          // nested BackdropFilter would force a second
                          // saveLayer and re-blur the same pixels.
                          child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.03),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AevraColors.line),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(v.platform, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AevraColors.lime)),
                                  Text('${v.qualityScore.round()}/100', style: const TextStyle(fontSize: 10, color: AevraColors.muted2)),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(v.caption, style: const TextStyle(fontSize: 12, color: AevraColors.text, height: 1.4)),
                            ],
                          ),
                          ),
                        );
                      },
                    ),
            ),
            if (campaign.status == 'awaiting_approval') ...[
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        AevraServices.maybeOf(context)?.sound.alert();
                        HapticFeedback.mediumImpact();
                        state.decide(campaign.id, 'reject');
                        Navigator.pop(context);
                      },
                      child: const Text('Request changes'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: FilledButton(
                      style: FilledButton.styleFrom(backgroundColor: AevraColors.lime, foregroundColor: AevraColors.onAccent),
                      onPressed: () {
                        AevraServices.celebrate(context);
                        state.decide(campaign.id, 'approve');
                        Navigator.pop(context);
                      },
                      child: const Text('Approve'),
                    ),
                  ),
                ],
              ),
            ],
          ],
          ),
        ),
      ),
    );
  }
}
