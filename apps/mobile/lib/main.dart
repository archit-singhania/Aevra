import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/analytics_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/campaigns_screen.dart';
import 'screens/overview_screen.dart';
import 'screens/schedule_screen.dart';
import 'state/app_state.dart';
import 'theme/aevra_theme.dart';
import 'widgets/shader_background.dart';

void main() => runApp(const AevraApp());

class AevraApp extends StatefulWidget {
  const AevraApp({super.key});

  @override
  State<AevraApp> createState() => _AevraAppState();
}

class _AevraAppState extends State<AevraApp> {
  late final AppState state;
  bool darkMode = true;

  @override
  void initState() {
    super.initState();
    state = AppState();
    state.hydrate();
  }

  @override
  void dispose() {
    state.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aevra',
      debugShowCheckedModeBanner: false,
      theme: darkMode ? AevraTheme.dark : AevraTheme.light,
      home: AnimatedBuilder(
        animation: state,
        builder: (context, _) {
          if (!state.hydrated) {
            return Scaffold(
              backgroundColor: AevraColors.bg,
              body: Stack(
                children: [
                  const Positioned.fill(child: RepaintBoundary(child: ShaderBackground())),
                  const Center(
                    child: CircularProgressIndicator(strokeWidth: 2, color: AevraColors.lime),
                  ),
                ],
              ),
            );
          }
          return AnimatedSwitcher(
            duration: const Duration(milliseconds: 320),
            switchInCurve: Curves.easeOutCubic,
            switchOutCurve: Curves.easeInCubic,
            transitionBuilder: (child, animation) =>
                FadeTransition(opacity: animation, child: child),
            child: state.authenticated
                ? MobileShell(
                    key: const ValueKey('shell'),
                    state: state,
                    darkMode: darkMode,
                    onToggleTheme: () => setState(() => darkMode = !darkMode),
                  )
                : AuthScreen(key: const ValueKey('auth'), state: state),
          );
        },
      ),
    );
  }
}

class MobileShell extends StatefulWidget {
  const MobileShell({super.key, required this.state, required this.darkMode, required this.onToggleTheme});

  final AppState state;
  final bool darkMode;
  final VoidCallback onToggleTheme;

  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  int index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      OverviewScreen(state: widget.state),
      CampaignsScreen(state: widget.state),
      ScheduleScreen(state: widget.state),
      AnalyticsScreen(state: widget.state),
    ];

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
                _TopBar(
                  title: _titles[index],
                  state: widget.state,
                  darkMode: widget.darkMode,
                  onToggleTheme: widget.onToggleTheme,
                ),
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
                    child: KeyedSubtree(key: ValueKey(index), child: pages[index]),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) {
          HapticFeedback.selectionClick();
          setState(() => index = value);
        },
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
  const _TopBar({required this.title, required this.state, required this.darkMode, required this.onToggleTheme});

  final String title;
  final AppState state;
  final bool darkMode;
  final VoidCallback onToggleTheme;

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
            onPressed: () => state.load(),
            icon: const Icon(Icons.refresh_outlined, size: 20),
            color: AevraColors.muted,
          ),
          IconButton(
            tooltip: darkMode ? 'Use light theme' : 'Use dark theme',
            onPressed: onToggleTheme,
            icon: Icon(darkMode ? Icons.light_mode_outlined : Icons.dark_mode_outlined, size: 20),
            color: AevraColors.muted,
          ),
          IconButton(
            onPressed: () => state.signOut(),
            icon: const Icon(Icons.logout_outlined, size: 20),
            color: AevraColors.muted,
          ),
        ],
      ),
    );
  }
}
