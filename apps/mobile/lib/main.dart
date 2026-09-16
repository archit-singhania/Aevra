import 'package:flutter/material.dart';

void main() => runApp(const AevraApp());

class AevraApp extends StatelessWidget {
  const AevraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aevra',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6D5EF7), brightness: Brightness.dark),
        useMaterial3: true,
      ),
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
  final pages = const [
    _OverviewPage(),
    _CampaignsPage(),
    _SchedulePage(),
    _AnalyticsPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Aevra')),
      body: pages[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.space_dashboard_outlined), label: 'Overview'),
          NavigationDestination(icon: Icon(Icons.auto_awesome_outlined), label: 'Campaigns'),
          NavigationDestination(icon: Icon(Icons.schedule_outlined), label: 'Schedule'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), label: 'Analytics'),
        ],
      ),
    );
  }
}

class _OverviewPage extends StatelessWidget {
  const _OverviewPage();
  @override
  Widget build(BuildContext context) => const _MetricList(title: 'Workspace overview', values: ['3 active campaigns', '12 approved variants', '6 connected channels']);
}

class _CampaignsPage extends StatelessWidget {
  const _CampaignsPage();
  @override
  Widget build(BuildContext context) => const _MetricList(title: 'Campaigns', values: ['Launch campaign', 'Product education', 'Community stories']);
}

class _SchedulePage extends StatelessWidget {
  const _SchedulePage();
  @override
  Widget build(BuildContext context) => const _MetricList(title: 'Schedule', values: ['No failed jobs', 'Next post in 2h 14m', 'Approval queue clear']);
}

class _AnalyticsPage extends StatelessWidget {
  const _AnalyticsPage();
  @override
  Widget build(BuildContext context) => const _MetricList(title: 'Analytics', values: ['7.5% engagement rate', 'LinkedIn is leading', 'Metrics synced today']);
}

class _MetricList extends StatelessWidget {
  const _MetricList({required this.title, required this.values});
  final String title;
  final List<String> values;
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(20), children: [Text(title, style: Theme.of(context).textTheme.headlineSmall), const SizedBox(height: 20), ...values.map((value) => Card(child: ListTile(leading: const Icon(Icons.check_circle_outline), title: Text(value))))]);
}
