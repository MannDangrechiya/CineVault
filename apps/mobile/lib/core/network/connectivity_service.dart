// CineVault OS — Connectivity & Auto-Sync Reconnect Manager (Phase 9.9 — P3 Fix)
// Listens to real OS network state changes via connectivity_plus and triggers sync upon reconnection.

import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ConnectivityService {
  bool _isOnline;
  final StreamController<bool> _statusController = StreamController<bool>.broadcast();
  final StreamController<void> _reconnectController = StreamController<void>.broadcast();
  StreamSubscription<List<ConnectivityResult>>? _subscription;

  Timer? _debounceTimer;
  DateTime? _lastSyncTriggeredAt;
  static const Duration _debounceDuration = Duration(milliseconds: 1000);

  ConnectivityService({bool initialOnline = true, bool enableOsListener = true})
      : _isOnline = initialOnline {
    if (enableOsListener) {
      _initConnectivityListener();
    }
  }

  bool get isOnline => _isOnline;
  Stream<bool> get statusStream => _statusController.stream;
  Stream<void> get reconnectStream => _reconnectController.stream;

  void _initConnectivityListener() {
    try {
      Connectivity().checkConnectivity().then(_handleConnectivityChange).catchError((_) {});
      _subscription = Connectivity().onConnectivityChanged.listen(
        _handleConnectivityChange,
        onError: (_) {},
      );
    } catch (_) {
      // Platform channels unavailable in headless unit test environment
    }
  }

  void _handleConnectivityChange(List<ConnectivityResult> results) {
    final hasConnection = results.any((result) => result != ConnectivityResult.none);
    updateConnectivity(hasConnection);
  }

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
    _subscription?.cancel();
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
