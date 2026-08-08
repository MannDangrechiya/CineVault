// CineVault OS — Catalog Screen (8.1)
// Displays canonical title catalog grid with responsive layout & accessible accessibility attributes

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/catalog_provider.dart';
import 'title_detail_screen.dart';

class CatalogScreen extends ConsumerWidget {
  const CatalogScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catalogState = ref.watch(catalogProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CineVault Catalog'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh catalog',
            onPressed: () => ref.read(catalogProvider.notifier).fetchTitles(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips Container
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  Semantics(
                    label: 'Filter All Types',
                    selected: catalogState.selectedContentType == null,
                    child: FilterChip(
                      label: const Text('All Types'),
                      selected: catalogState.selectedContentType == null,
                      onSelected: (_) => ref.read(catalogProvider.notifier).fetchTitles(contentType: null),
                      selectedColor: AppTheme.primaryViolet,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Semantics(
                    label: 'Filter Movies Only',
                    selected: catalogState.selectedContentType == 'MOVIE',
                    child: FilterChip(
                      label: const Text('Movies'),
                      selected: catalogState.selectedContentType == 'MOVIE',
                      onSelected: (_) => ref.read(catalogProvider.notifier).fetchTitles(contentType: 'MOVIE'),
                      selectedColor: AppTheme.primaryViolet,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Semantics(
                    label: 'Filter TV Series Only',
                    selected: catalogState.selectedContentType == 'TV_SERIES',
                    child: FilterChip(
                      label: const Text('TV Series'),
                      selected: catalogState.selectedContentType == 'TV_SERIES',
                      onSelected: (_) => ref.read(catalogProvider.notifier).fetchTitles(contentType: 'TV_SERIES'),
                      selectedColor: AppTheme.primaryViolet,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Main Content Grid / Loading / Error
          Expanded(
            child: catalogState.isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      semanticsLabel: 'Loading catalog titles',
                    ),
                  )
                : catalogState.errorMessage != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.error_outline, color: AppTheme.stateError, size: 48),
                              const SizedBox(height: 12),
                              Text(
                                catalogState.errorMessage!,
                                style: textTheme.bodyMedium,
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: () => ref.read(catalogProvider.notifier).fetchTitles(),
                                child: const Text('Retry'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : catalogState.titles.isEmpty
                        ? Center(
                            child: Text(
                              'No canonical titles match selected criteria.',
                              style: textTheme.bodyLarge,
                            ),
                          )
                        : LayoutBuilder(
                            builder: (context, constraints) {
                              // Responsive Breakpoints
                              final crossAxisCount = constraints.maxWidth > 900
                                  ? 4
                                  : constraints.maxWidth > 600
                                      ? 3
                                      : 2;

                              return GridView.builder(
                                padding: const EdgeInsets.all(16),
                                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: crossAxisCount,
                                  childAspectRatio: 0.68,
                                  crossAxisSpacing: 16,
                                  mainAxisSpacing: 16,
                                ),
                                itemCount: catalogState.titles.length,
                                itemBuilder: (context, index) {
                                  final title = catalogState.titles[index];
                                  return Semantics(
                                    label: '${title.primaryTitle}, ${title.contentType}, released ${title.releaseYear ?? "unknown"}',
                                    button: true,
                                    child: InkWell(
                                      onTap: () {
                                        Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                            builder: (_) => TitleDetailScreen(titleId: title.titleId),
                                          ),
                                        );
                                      },
                                      child: Card(
                                        clipBehavior: Clip.antiAlias,
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Expanded(
                                              child: Container(
                                                color: AppTheme.cardElevated,
                                                child: Center(
                                                  child: Icon(
                                                    title.contentType == 'MOVIE'
                                                        ? Icons.movie
                                                        : Icons.tv,
                                                    size: 48,
                                                    color: AppTheme.primaryLightViolet,
                                                  ),
                                                ),
                                              ),
                                            ),
                                            Padding(
                                              padding: const EdgeInsets.all(10.0),
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  Text(
                                                    title.primaryTitle,
                                                    style: textTheme.titleMedium,
                                                    maxLines: 1,
                                                    overflow: TextOverflow.ellipsis,
                                                  ),
                                                  const SizedBox(height: 4),
                                                  Row(
                                                    children: [
                                                      Text(
                                                        '${title.releaseYear ?? "N/A"}',
                                                        style: textTheme.bodySmall,
                                                      ),
                                                      const Spacer(),
                                                      Container(
                                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                        decoration: BoxDecoration(
                                                          color: AppTheme.primaryViolet.withValues(alpha: 0.2),
                                                          borderRadius: BorderRadius.circular(4),
                                                        ),
                                                        child: Text(
                                                          title.contentType,
                                                          style: const TextStyle(fontSize: 10, color: AppTheme.primaryLightViolet),
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
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
