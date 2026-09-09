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
import 'presentation/screens/swipe_discovery_screen.dart';
import 'presentation/screens/sync_status_screen.dart';
import 'presentation/screens/library_screen.dart';
import 'presentation/screens/control_room_screen.dart';
import 'presentation/screens/social_hub_screen.dart';
import 'presentation/screens/clubs_screen.dart';
import 'presentation/screens/invite_screen.dart';
import 'presentation/screens/import_screen.dart';
import 'presentation/screens/settings_screen.dart';
import 'presentation/widgets/glass/glass.dart';

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
      const SwipeDiscoveryScreen(),
      const SearchScreen(),
      const RecommendationsScreen(),
      const AiAssistantScreen(),
      const LibraryScreen(),
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
        icon: Icon(Icons.style_outlined),
        activeIcon: Icon(Icons.style),
        label: 'Swipe',
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
        icon: Icon(Icons.local_library_outlined),
        activeIcon: Icon(Icons.local_library),
        label: 'Library',
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
      // Note: extendBodyBehindAppBar is intentionally NOT set here — each
      // embedded screen below has its own nested Scaffold+AppBar (see
      // presentation/screens/*), so extending this outer body behind this
      // outer app bar would overlap it with the inner screen's own app bar.
      // extendBody is safe: each screen's own body content (lists/grids)
      // naturally scrolls behind the shared GlassBottomNav below.
      extendBody: true,
      appBar: GlassAppBar(
        title: const Text('CineVault OS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.people_outline),
            tooltip: 'Social Hub',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SocialHubScreen()),
              );
            },
          ),
          // Secondary screens (clubs/challenges, invite/referrals, data
          // import) live behind a "more" menu rather than as their own
          // bottom-nav tabs or app-bar icons — the bar is already crowded
          // (7-8 tabs), and none of these are visited as often as the tabs.
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            tooltip: 'More',
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'clubs',
                child: ListTile(
                  leading: Icon(Icons.groups_outlined),
                  title: Text('Watch Clubs'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'invite',
                child: ListTile(
                  leading: Icon(Icons.person_add_outlined),
                  title: Text('Invite a Friend'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'import',
                child: ListTile(
                  leading: Icon(Icons.upload_file_outlined),
                  title: Text('Import Watch History'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'settings',
                child: ListTile(
                  leading: Icon(Icons.settings_outlined),
                  title: Text('Settings'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ],
            onSelected: (value) {
              final Widget screen = switch (value) {
                'clubs' => const ClubsScreen(),
                'invite' => const InviteScreen(),
                'import' => const ImportScreen(),
                'settings' => const SettingsScreen(),
                _ => throw StateError('Unknown menu selection: $value'),
              };
              Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
            },
          ),
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
      bottomNavigationBar: GlassBottomNav(
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
