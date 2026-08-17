// CineVault OS — Main Client Entry Point
// Initializes Riverpod ProviderScope and boots CineVaultApp

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  runApp(
    const ProviderScope(
      child: CineVaultApp(),
    ),
  );
}
