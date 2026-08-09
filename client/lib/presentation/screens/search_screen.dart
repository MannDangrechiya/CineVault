// CineVault OS — Catalog Search Screen (8.3)
// Real-time catalog search with filters and local recent query history

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/remote/search_remote_datasource.dart';
import '../../domain/entities/title.dart';
import '../providers/catalog_provider.dart';
import 'title_detail_screen.dart';

final searchDatasourceProvider = Provider<SearchRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return SearchRemoteDatasource(apiClient);
});

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  List<CanonicalTitleEntity> _searchResults = [];
  bool _isSearching = false;
  String? _errorMessage;

  Future<void> _performSearch(String query) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _isSearching = true;
      _errorMessage = null;
    });

    try {
      final datasource = ref.read(searchDatasourceProvider);
      final results = await datasource.searchCatalog(query: query);
      setState(() {
        _searchResults = results;
        _isSearching = false;
      });
    } catch (e) {
      setState(() {
        _isSearching = false;
        _errorMessage = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Catalog Search (8.3)'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search titles, people, alternate names...',
                prefixIcon: const Icon(Icons.search, color: AppTheme.primaryLightViolet),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: () => _performSearch(_searchController.text),
                ),
              ),
              onSubmitted: _performSearch,
            ),
          ),
          Expanded(
            child: _isSearching
                ? const Center(child: CircularProgressIndicator(semanticsLabel: 'Searching catalog'))
                : _errorMessage != null
                    ? Center(child: Text(_errorMessage!, style: textTheme.bodyLarge))
                    : _searchResults.isEmpty
                        ? Center(
                            child: Text(
                              _searchController.text.isEmpty
                                  ? 'Enter a query to search CineVault catalog.'
                                  : 'No results found for "${_searchController.text}".',
                              style: textTheme.bodyMedium,
                            ),
                          )
                        : ListView.builder(
                            itemCount: _searchResults.length,
                            itemBuilder: (context, index) {
                              final item = _searchResults[index];
                              return ListTile(
                                leading: Container(
                                  width: 40,
                                  height: 56,
                                  decoration: BoxDecoration(
                                    color: AppTheme.cardElevated,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  clipBehavior: Clip.antiAlias,
                                  child: item.posterUrl != null && item.posterUrl!.isNotEmpty
                                      ? Image.network(
                                          item.posterUrl!,
                                          fit: BoxFit.cover,
                                          errorBuilder: (context, error, stackTrace) => Icon(
                                            item.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                                            color: AppTheme.primaryViolet,
                                            size: 24,
                                          ),
                                        )
                                      : Icon(
                                          item.contentType == 'MOVIE' ? Icons.movie : Icons.tv,
                                          color: AppTheme.primaryViolet,
                                          size: 24,
                                        ),
                                ),
                                title: Text(item.primaryTitle, style: textTheme.titleMedium),
                                subtitle: Text('${item.contentType} • ${item.releaseYear ?? "N/A"}'),
                                trailing: const Icon(Icons.chevron_right),
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => TitleDetailScreen(titleId: item.titleId),
                                    ),
                                  );
                                },
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}
