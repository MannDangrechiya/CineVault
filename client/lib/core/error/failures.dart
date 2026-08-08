// CineVault OS — Client Error & Failure Hierarchy
// Maps backend HTTP/RPC errors into user-safe failure objects without exposing system details

abstract class Failure {
  final String message;
  final int? statusCode;

  const Failure(this.message, {this.statusCode});

  @override
  String toString() => '$runtimeType: $message${statusCode != null ? " (Code: $statusCode)" : ""}';
}

class NetworkFailure extends Failure {
  const NetworkFailure([String message = 'Network connection unavailable. Please check your connectivity.'])
      : super(message);
}

class OfflineFailure extends Failure {
  const OfflineFailure([String message = 'Device is offline. Action queued in local outbox.'])
      : super(message);
}

class UnauthorizedFailure extends Failure {
  const UnauthorizedFailure([String message = 'Authentication session expired. Please sign in again.', int statusCode = 401])
      : super(message, statusCode: statusCode);
}

class ForbiddenFailure extends Failure {
  const ForbiddenFailure([String message = 'Access denied. You do not have permission for this resource.', int statusCode = 403])
      : super(message, statusCode: statusCode);
}

class NotFoundFailure extends Failure {
  const NotFoundFailure([String message = 'Requested catalog item or resource could not be found.', int statusCode = 404])
      : super(message, statusCode: statusCode);
}

class ConflictFailure extends Failure {
  const ConflictFailure([String message = 'Personal record update conflict detected.', int statusCode = 409])
      : super(message, statusCode: statusCode);
}

class ValidationFailure extends Failure {
  const ValidationFailure([String message = 'Input validation failed. Please check your entries.', int statusCode = 422])
      : super(message, statusCode: statusCode);
}

class ServerFailure extends Failure {
  const ServerFailure([String message = 'CineVault service experienced a temporary issue.', int statusCode = 500])
      : super(message, statusCode: statusCode);
}

class UnknownFailure extends Failure {
  const UnknownFailure([String message = 'An unexpected error occurred. Please try again.'])
      : super(message);
}
