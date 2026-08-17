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
  const NetworkFailure([super.message = 'Network connection unavailable. Please check your connectivity.']);
}

class OfflineFailure extends Failure {
  const OfflineFailure([super.message = 'Device is offline. Action queued in local outbox.']);
}

class UnauthorizedFailure extends Failure {
  const UnauthorizedFailure([super.message = 'Authentication session expired. Please sign in again.', int statusCode = 401])
      : super(statusCode: statusCode);
}

class ForbiddenFailure extends Failure {
  const ForbiddenFailure([super.message = 'Access denied. You do not have permission for this resource.', int statusCode = 403])
      : super(statusCode: statusCode);
}

class NotFoundFailure extends Failure {
  const NotFoundFailure([super.message = 'Requested catalog item or resource could not be found.', int statusCode = 404])
      : super(statusCode: statusCode);
}

class ConflictFailure extends Failure {
  const ConflictFailure([super.message = 'Personal record update conflict detected.', int statusCode = 409])
      : super(statusCode: statusCode);
}

class ValidationFailure extends Failure {
  const ValidationFailure([super.message = 'Input validation failed. Please check your entries.', int statusCode = 422])
      : super(statusCode: statusCode);
}

class ServerFailure extends Failure {
  const ServerFailure([super.message = 'CineVault service experienced a temporary issue.', int statusCode = 500])
      : super(statusCode: statusCode);
}

class UnknownFailure extends Failure {
  const UnknownFailure([super.message = 'An unexpected error occurred. Please try again.']);
}
