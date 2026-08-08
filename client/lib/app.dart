// CineVault OS — Main Client Shell (Build Unit 8.11)
// Clean navigation shell connecting Catalog, Search, Recommendations, AI Assistant & Offline Outbox

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'presentation/screens/catalog_screen.dart';
import 'presentation/screens/search_screen.dart';
import 'presentation/screens/recommendations_screen.dart';
import 'presentation/screens/ai_assistant_screen.dart';
import 'presentation/screens/sync_status_screen.dart';

class CineVaultApp extends StatelessWidget {
  const CineVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CineVault OS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const MainShellScreen(),
    );
  }
}

class MainShellScreen extends ConsumerStatefulWidget {
  const MainShellScreen({super.key});

  @override
  ConsumerState<MainShellScreen> createState() => _MainShellScreenState();
}

class _MainShellScreenState extends ConsumerState<MainShellScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    CatalogScreen(),
    SearchScreen(),
    RecommendationsScreen(),
    AiAssistantScreen(),
    SyncStatusScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.movie_creation_outlined),
            activeIcon: Icon(Icons.movie_creation),
            label: 'Catalog',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.search_outlined),
            activeIcon: Icon(Icons.search),
            label: 'Search',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.auto_awesome_outlined),
            activeIcon: Icon(Icons.auto_awesome),
            label: 'For You',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.forum_outlined),
            activeIcon: Icon(Icons.forum),
            label: 'Assistant',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.sync_outlined),
            activeIcon: Icon(Icons.sync),
            label: 'Outbox',
          ),
        ],
      ),
    );
  }
}
