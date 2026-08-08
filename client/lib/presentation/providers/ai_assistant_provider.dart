// CineVault OS — AI Assistant Riverpod Provider (8.8)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/remote/ai_assistant_remote_datasource.dart';
import '../../domain/entities/ai_assistant.dart';
import 'catalog_provider.dart';

final aiAssistantDatasourceProvider = Provider<AiAssistantRemoteDatasource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AiAssistantRemoteDatasource(apiClient);
});

class AiAssistantState {
  final bool isProcessing;
  final List<AiResponseEntity> chatHistory;
  final String? errorMessage;

  const AiAssistantState({
    this.isProcessing = false,
    this.chatHistory = const [],
    this.errorMessage,
  });

  AiAssistantState copyWith({
    bool? isProcessing,
    List<AiResponseEntity>? chatHistory,
    String? errorMessage,
  }) {
    return AiAssistantState(
      isProcessing: isProcessing ?? this.isProcessing,
      chatHistory: chatHistory ?? this.chatHistory,
      errorMessage: errorMessage,
    );
  }
}

class AiAssistantNotifier extends StateNotifier<AiAssistantState> {
  final AiAssistantRemoteDatasource _datasource;

  AiAssistantNotifier(this._datasource) : super(const AiAssistantState());

  Future<void> submitQuery(String queryText) async {
    if (queryText.trim().isEmpty) return;

    state = state.copyWith(isProcessing: true, errorMessage: null);
    try {
      final response = await _datasource.processQuery(queryText);
      state = state.copyWith(
        isProcessing: false,
        chatHistory: [...state.chatHistory, response],
      );
    } catch (e) {
      state = state.copyWith(
        isProcessing: false,
        errorMessage: e.toString(),
      );
    }
  }
}

final aiAssistantProvider = StateNotifierProvider<AiAssistantNotifier, AiAssistantState>((ref) {
  final datasource = ref.watch(aiAssistantDatasourceProvider);
  return AiAssistantNotifier(datasource);
});
