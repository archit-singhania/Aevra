import 'package:flutter/material.dart';
import 'screens/analytics_screen.dart';
import 'screens/campaigns_screen.dart';
import 'screens/overview_screen.dart';
import 'screens/schedule_screen.dart';
import 'theme/aevra_theme.dart';
import 'widgets/shader_background.dart';

void main() => runApp(const AevraApp());

class AevraApp extends StatelessWidget {
  const AevraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aevra',
      debugShowCheckedModeBanner: false,
      theme: AevraTheme.dark,
      home: const MobileShell(),
    );
  }
}

class MobileShell extends StatefulWidget {
  const MobileShell({super.key});

  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  int index = 0;

  static const _pages = [
    OverviewScreen(),
    CampaignsScreen(),
    ScheduleScreen(),
    AnalyticsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AevraColors.bg,
      extendBodyBehindAppBar: true,
      extendBody: true,
      body: Stack(
        children: [
          // Animated GPU background, behind everything.
          const Positioned.fill(child: RepaintBoundary(child: ShaderBackground())),
          SafeArea(
            child: Column(
              children: [
                _TopBar(title: _titles[index]),
                Expanded(
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 260),
                    switchInCurve: Curves.easeOutCubic,
                    switchOutCurve: Curves.easeInCubic,
                    transitionBuilder: (child, animation) {
                      final fade = animation;
                      final slide = Tween<Offset>(
                        begin: const Offset(0, 0.02),
                        end: Offset.zero,
                      ).animate(animation);
                      return FadeTransition(
                        opacity: fade,
                        child: SlideTransition(position: slide, child: child),
                      );
                    },
                    child: KeyedSubtree(key: ValueKey(index), child: _pages[index]),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        backgroundColor: Colors.transparent,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.space_dashboard_outlined), label: 'Overview'),
          NavigationDestination(icon: Icon(Icons.auto_awesome_outlined), label: 'Campaigns'),
          NavigationDestination(icon: Icon(Icons.schedule_outlined), label: 'Schedule'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), label: 'Analytics'),
        ],
      ),
    );
  }

  static const _titles = ['Overview', 'Campaigns', 'Schedule', 'Analytics'];
}

/// Custom glass top bar — the mobile equivalent of the web app's `.topbar`.
class _TopBar extends StatelessWidget {
  const _TopBar({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 16, 12),
      child: Row(
        children: [
          Container(
            width: 26,
            height: 26,
            decoration: BoxDecoration(
              border: Border.all(color: AevraColors.lime.withOpacity(0.55)),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(7),
                topRight: Radius.circular(7),
                bottomRight: Radius.circular(11),
                bottomLeft: Radius.circular(7),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Text(
            title,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600, letterSpacing: -0.01),
          ),
          const Spacer(),
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.notifications_outlined, size: 20),
            color: AevraColors.muted,
          ),
        ],
      ),
    );
  }
}
