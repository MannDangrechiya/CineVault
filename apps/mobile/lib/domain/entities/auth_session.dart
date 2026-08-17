// CineVault OS — Auth Session Domain Entity (Phase 9.8)

class AuthSessionEntity {
  final String accessToken;
  final String refreshToken;
  final String userId;
  final String email;
  final List<String> roles;

  const AuthSessionEntity({
    required this.accessToken,
    required this.refreshToken,
    required this.userId,
    required this.email,
    required this.roles,
  });

  factory AuthSessionEntity.fromJson(Map<String, dynamic> json) {
    return AuthSessionEntity(
      accessToken: json['access_token'] ?? '',
      refreshToken: json['refresh_token'] ?? '',
      userId: json['user_id'] ?? '',
      email: json['email'] ?? '',
      roles: json['roles'] != null ? List<String>.from(json['roles']) : [],
    );
  }
}
