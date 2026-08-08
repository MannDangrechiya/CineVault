// CineVault OS — Client UUID Generator
// Generates UUIDv7 identifiers for client outbox mutations (ADR-004)

import 'package:uuid/uuid.dart';

class UuidUtil {
  static const Uuid _uuid = Uuid();

  /// Generates a time-ordered UUIDv7 mutation ID for offline outbox tracking
  static String generateMutationId() {
    return _uuid.v7();
  }

  /// Generates a correlation ID header for network traceability
  static String generateCorrelationId() {
    return _uuid.v4();
  }
}
