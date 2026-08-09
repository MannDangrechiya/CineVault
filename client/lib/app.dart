// CineVault OS — Main Client Shell & Authentication Root (Build Unit 8.11)
// Clean navigation shell connecting Catalog, Search, Recommendations, AI Assistant, Offline Outbox, Control Room & Login Gate

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'presentation/providers/auth_provider.dart';
import 'presentation/providers/control_room_provider.dart';
import 'presentation/screens/login_screen.dart';
import 'presentation/screens/catalog_screen.dart';
import 'presentation/screens/search_screen.dart';
import 'presentation/screens/recommendations_screen.dart';
import 'presentation/screens/ai_assistant_screen.dart';
import 'presentation/screens/sync_status_screen.dart';
import 'presentation/screens/control_room_screen.dart';

class CineVaultApp extends StatelessWidget {
  const CineVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CineVault OS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const RootAuthGate(),
    );
  }
}

class RootAuthGate extends ConsumerWidget {
  const RootAuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    if (authState.isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (!authState.isAuthenticated) {
      return const LoginScreen();
    }

    return const MainShellScreen();
  }
}

class MainShellScreen extends ConsumerStatefulWidget {
  const MainShellScreen({super.key});

  @override
  ConsumerState<MainShellScreen> createState() => _MainShellScreenState();
}

class _MainShellScreenState extends ConsumerState<MainShellScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final curatorAsync = ref.watch(curatorRoleProvider);
    final isCurator = curatorAsync.asData?.value ?? false;

    final screens = <Widget>[
      const CatalogScreen(),
      const SearchScreen(),
      const RecommendationsScreen(),
      const AiAssistantScreen(),
      const SyncStatusScreen(),
      if (isCurator) const ControlRoomScreen(),
    ];

    final navItems = <BottomNavigationBarItem>[
      const BottomNavigationBarItem(
        icon: Icon(Icons.movie_creation_outlined),
        activeIcon: Icon(Icons.movie_creation),
        label: 'Catalog',
      ),
      const BottomNavigationBarItem(
        icon: Icon(Icons.search_outlined),
        activeIcon: Icon(Icons.search),
        label: 'Search',
      ),
      const BottomNavigationBarItem(
        icon: Icon(Icons.auto_awesome_outlined),
        activeIcon: Icon(Icons.auto_awesome),
        label: 'For You',
      ),
      const BottomNavigationBarItem(
        icon: Icon(Icons.forum_outlined),
        activeIcon: Icon(Icons.forum),
        label: 'Assistant',
      ),
      const BottomNavigationBarItem(
        icon: Icon(Icons.sync_outlined),
        activeIcon: Icon(Icons.sync),
        label: 'Outbox',
      ),
      if (isCurator)
        const BottomNavigationBarItem(
          icon: Icon(Icons.admin_panel_settings_outlined),
          activeIcon: Icon(Icons.admin_panel_settings),
          label: 'Control',
        ),
    ];

    final safeIndex = _currentIndex < screens.length ? _currentIndex : 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CineVault OS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () {
              ref.read(authProvider.notifier).logout();
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: safeIndex,
        children: screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: safeIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: navItems,
      ),
    );
  }
}
