import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design tokens shared across the mobile app — mirrors the web app's
/// CSS custom properties (apps/web/app/globals.css) so both platforms read
/// as one product.
class AevraColors {
  AevraColors._();

  static const bg = Color(0xFF07090D);
  static const panel = Color(0xFF0D1016);
  static const line = Color(0x16FFFFFF);
  static const lineStrong = Color(0x24FFFFFF);
  static const text = Color(0xFFF4F6F2);
  static const muted = Color(0xFF8D949F);
  static const muted2 = Color(0xFF626A76);
  static const lime = Color(0xFFB5FF5E);
  static const violet = Color(0xFFAA8CFF);
  static const cyan = Color(0xFF65DFEE);
}

class AevraTheme {
  AevraTheme._();

  static ThemeData get dark {
    final base = ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AevraColors.bg,
      colorScheme: const ColorScheme.dark(
        brightness: Brightness.dark,
        primary: AevraColors.lime,
        onPrimary: Color(0xFF07100A),
        secondary: AevraColors.violet,
        tertiary: AevraColors.cyan,
        surface: AevraColors.panel,
        onSurface: AevraColors.text,
        error: Color(0xFFFF6262),
      ),
      useMaterial3: true,
    );

    final textTheme = GoogleFonts.interTextTheme(base.textTheme).apply(
      bodyColor: AevraColors.text,
      displayColor: AevraColors.text,
    );

    return base.copyWith(
      textTheme: textTheme.copyWith(
        headlineSmall: textTheme.headlineSmall?.copyWith(
          fontWeight: FontWeight.w600,
          letterSpacing: -0.02,
        ),
        titleMedium: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
        bodySmall: textTheme.bodySmall?.copyWith(color: AevraColors.muted),
      ),
      splashFactory: NoSplash.splashFactory,
      highlightColor: Colors.transparent,
      dividerColor: AevraColors.line,
      iconTheme: const IconThemeData(color: AevraColors.muted, size: 20),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: AevraColors.panel.withOpacity(0.72),
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AevraColors.line),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.transparent,
        elevation: 0,
        indicatorColor: AevraColors.lime.withOpacity(0.12),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 11,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
            color: selected ? Colors.white : AevraColors.muted,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(color: selected ? AevraColors.lime : AevraColors.muted, size: 22);
        }),
      ),
    );
  }

  static ThemeData get light {
    final base = ThemeData(
      brightness: Brightness.light,
      scaffoldBackgroundColor: const Color(0xFFF5F7F2),
      colorScheme: const ColorScheme.light(
        primary: Color(0xFF427A00),
        onPrimary: Colors.white,
        secondary: Color(0xFF6848B8),
        tertiary: Color(0xFF167A86),
        surface: Colors.white,
        onSurface: Color(0xFF142016),
        error: Color(0xFFB42318),
      ),
      useMaterial3: true,
    );
    final textTheme = GoogleFonts.interTextTheme(base.textTheme).apply(
      bodyColor: const Color(0xFF142016),
      displayColor: const Color(0xFF142016),
    );
    return base.copyWith(
      textTheme: textTheme.copyWith(bodySmall: textTheme.bodySmall?.copyWith(color: const Color(0xFF566358))),
      splashFactory: NoSplash.splashFactory,
      highlightColor: Colors.transparent,
      dividerColor: const Color(0x1A142016),
      cardTheme: CardThemeData(
        color: Colors.white.withOpacity(0.88),
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0x1A142016)),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.white.withOpacity(0.9),
        indicatorColor: const Color(0x26427A00),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(fontSize: 11, fontWeight: selected ? FontWeight.w600 : FontWeight.w500, color: selected ? const Color(0xFF315C00) : const Color(0xFF566358));
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(color: selected ? const Color(0xFF427A00) : const Color(0xFF566358), size: 22);
        }),
      ),
    );
  }
}
