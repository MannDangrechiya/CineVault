// CineVault OS — Connectivity & Auto-Sync Reconnect Manager (Phase 9.9)

import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ConnectivityService {
  bool _isOnline;
  final StreamController<bool> _statusController = StreamController<bool>.broadcast();
  final StreamController<void> _reconnectController = StreamController<void>.broadcast();

  Timer? _debounceTimer;
  DateTime? _lastSyncTriggeredAt;
  static const Duration _debounceDuration = Duration(milliseconds: 1000);

  ConnectivityService({bool initialOnline = true}) : _isOnline = initialOnline;

  bool get isOnline => _isOnline;
  Stream<bool> get statusStream => _statusController.stream;
  Stream<void> get reconnectStream => _reconnectController.stream;

  void updateConnectivity(bool online) {
    if (_isOnline == online) return;

    final wasOffline = !_isOnline;
    _isOnline = online;
    _statusController.add(_isOnline);

    if (wasOffline && _isOnline) {
      _scheduleDebouncedReconnect();
    }
  }

  void _scheduleDebouncedReconnect() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(_debounceDuration, () {
      final now = DateTime.now();
      if (_lastSyncTriggeredAt == null ||
          now.difference(_lastSyncTriggeredAt!) >= _debounceDuration) {
        _lastSyncTriggeredAt = now;
        _reconnectController.add(null);
      }
    });
  }

  void dispose() {
    _debounceTimer?.cancel();
    _statusController.close();
    _reconnectController.close();
  }
}

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  final service = ConnectivityService();
  ref.onDispose(() => service.dispose());
  return service;
});
