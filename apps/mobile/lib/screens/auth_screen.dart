import 'package:flutter/material.dart';

import '../state/app_state.dart';
import '../theme/aevra_theme.dart';
import '../widgets/glass_card.dart';
import '../widgets/shader_background.dart';

/// The mobile counterpart of the web app's `.live-auth` screen — same
/// shader background + glass auth card, same login/register fields.
class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key, required this.state});

  final AppState state;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();
  final _org = TextEditingController();
  final _workspaceName = TextEditingController();

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _name.dispose();
    _org.dispose();
    _workspaceName.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (isLogin) {
      await widget.state.login(_email.text.trim(), _password.text);
    } else {
      await widget.state.register(
        email: _email.text.trim(),
        password: _password.text,
        displayName: _name.text.trim(),
        organizationName: _org.text.trim(),
        workspaceName: _workspaceName.text.trim(),
        timezone: DateTime.now().timeZoneName,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AevraColors.bg,
      body: Stack(
        children: [
          const Positioned.fill(child: RepaintBoundary(child: ShaderBackground())),
          SafeArea(
            child: AnimatedBuilder(
              animation: widget.state,
              builder: (context, _) {
                return SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(22, 40, 22, 32),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
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
                          const Text(
                            'AEVRA',
                            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, letterSpacing: 3),
                          ),
                        ],
                      ),
                      const SizedBox(height: 26),
                      const Text(
                        'Make every campaign feel\nlike your sharpest team\nmember made it.',
                        style: TextStyle(fontSize: 27, fontWeight: FontWeight.w600, height: 1.1, letterSpacing: -0.02),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Turn approved brand knowledge into evidence-backed, human-approved content operations.',
                        style: TextStyle(fontSize: 13, height: 1.5, color: AevraColors.muted),
                      ),
                      const SizedBox(height: 28),
                      GlassCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                _Tab(label: 'Sign in', active: isLogin, onTap: () => setState(() => isLogin = true)),
                                const SizedBox(width: 18),
                                _Tab(label: 'Create workspace', active: !isLogin, onTap: () => setState(() => isLogin = false)),
                              ],
                            ),
                            const SizedBox(height: 18),
                            Text(
                              isLogin ? 'Welcome back' : 'Start your Aevra workspace',
                              style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 16),
                            if (widget.state.error != null) ...[
                              _ErrorBanner(message: widget.state.error!),
                              const SizedBox(height: 12),
                            ],
                            if (!isLogin) ...[
                              _Field(label: 'Your name', controller: _name),
                              const SizedBox(height: 12),
                              _Field(label: 'Organization', controller: _org),
                              const SizedBox(height: 12),
                              _Field(label: 'Workspace', controller: _workspaceName),
                              const SizedBox(height: 12),
                            ],
                            _Field(label: 'Email', controller: _email, keyboardType: TextInputType.emailAddress),
                            const SizedBox(height: 12),
                            _Field(label: 'Password', controller: _password, obscure: true),
                            const SizedBox(height: 18),
                            SizedBox(
                              width: double.infinity,
                              child: FilledButton(
                                onPressed: widget.state.loading ? null : _submit,
                                style: FilledButton.styleFrom(
                                  backgroundColor: AevraColors.lime,
                                  foregroundColor: const Color(0xFF07100A),
                                  padding: const EdgeInsets.symmetric(vertical: 14),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
                                ),
                                child: widget.state.loading
                                    ? const SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF07100A)),
                                      )
                                    : Text(
                                        isLogin ? 'Enter workspace' : 'Create workspace',
                                        style: const TextStyle(fontWeight: FontWeight.w600),
                                      ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  const _Tab({required this.label, required this.active, required this.onTap});

  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: active ? AevraColors.lime : AevraColors.muted,
            ),
          ),
          const SizedBox(height: 6),
          Container(
            height: 2,
            width: 40,
            color: active ? AevraColors.lime : Colors.transparent,
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.label,
    required this.controller,
    this.obscure = false,
    this.keyboardType,
  });

  final String label;
  final TextEditingController controller;
  final bool obscure;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: AevraColors.muted2)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          obscureText: obscure,
          keyboardType: keyboardType,
          style: const TextStyle(fontSize: 13, color: AevraColors.text),
          decoration: InputDecoration(
            isDense: true,
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            filled: true,
            fillColor: const Color(0xFF0B1011),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(9),
              borderSide: const BorderSide(color: AevraColors.line),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(9),
              borderSide: const BorderSide(color: AevraColors.line),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(9),
              borderSide: const BorderSide(color: AevraColors.lime),
            ),
          ),
        ),
      ],
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFFF6262).withOpacity(0.1),
        borderRadius: BorderRadius.circular(9),
      ),
      child: Text(message, style: const TextStyle(fontSize: 11, color: Color(0xFFFFB4AA))),
    );
  }
}
