// CineVault OS — ClubDetailScreen Widget & Membership Gating Tests

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/core/theme/app_theme.dart';
import 'package:cinevault_client/domain/entities/auth_session.dart';
import 'package:cinevault_client/domain/entities/social.dart';
import 'package:cinevault_client/domain/repositories/auth_repository.dart';
import 'package:cinevault_client/domain/repositories/social_repository.dart';
import 'package:cinevault_client/presentation/providers/auth_provider.dart';
import 'package:cinevault_client/presentation/providers/social_provider.dart';
import 'package:cinevault_client/presentation/screens/club_detail_screen.dart';

class FakeSocialRepo implements SocialRepository {
  ClubDetailEntity? detailToReturn;
  List<ClubActivityEntity> feedToReturn = const [];
  bool joinClubCalled = false;

  @override
  Future<ClubDetailEntity> getWatchClub(String slug) async {
    if (detailToReturn != null) return detailToReturn!;
    throw Exception('Club not found');
  }

  @override
  Future<List<ClubActivityEntity>> getClubFeed(String slug, {int limit = 20}) async {
    return feedToReturn;
  }

  @override
  Future<ClubMembershipEntity> joinWatchClub(String slug) async {
    joinClubCalled = true;
    return const ClubMembershipEntity(
      clubId: 'club-1',
      userId: 'new-user',
      role: 'member',
      joinedAt: '2026-09-09T00:00:00Z',
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class FakeAuthRepo implements AuthRepository {
  final String? userId;
  FakeAuthRepo([this.userId]);

  @override
  Future<AuthSessionEntity?> getStoredSession() async {
    if (userId == null) return null;
    return AuthSessionEntity(
      accessToken: 'token',
      refreshToken: 'refresh',
      userId: userId!,
      email: 'member@cinevault.org',
      roles: const ['AuthenticatedUser'],
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  const sampleClub = WatchClubEntity(
    clubId: 'club-1',
    name: 'Sci-Fi Enthusiasts',
    slug: 'sci-fi-enthusiasts',
    createdBy: 'creator-user',
    description: 'A club dedicated to science fiction cinema.',
    memberCount: 2,
    createdAt: '2026-09-09T00:00:00Z',
  );

  const sampleMembers = [
    ClubMembershipEntity(
      clubId: 'club-1',
      userId: 'existing-member-id',
      userName: 'Bob',
      role: 'admin',
      joinedAt: '2026-09-09T00:00:00Z',
    ),
  ];

  const sampleDetail = ClubDetailEntity(
    club: sampleClub,
    members: sampleMembers,
  );

  Widget createTestWidget({
    required FakeSocialRepo socialRepo,
    required String? currentUserId,
  }) {
    return ProviderScope(
      overrides: [
        socialRepositoryProvider.overrideWithValue(socialRepo),
        authProvider.overrideWith((ref) => AuthNotifier(FakeAuthRepo(currentUserId))),
      ],
      child: MaterialApp(
        theme: AppTheme.darkTheme,
        home: const ClubDetailScreen(slug: 'sci-fi-enthusiasts'),
      ),
    );
  }

  testWidgets('Renders club details, member roster, and description', (tester) async {
    final repo = FakeSocialRepo()..detailToReturn = sampleDetail;

    await tester.pumpWidget(createTestWidget(
      socialRepo: repo,
      currentUserId: 'non-member-user',
    ));
    await tester.pumpAndSettle();

    expect(find.text('Sci-Fi Enthusiasts'), findsOneWidget);
    expect(find.text('A club dedicated to science fiction cinema.'), findsOneWidget);
    expect(find.text('Members (1)'), findsOneWidget);
    expect(find.text('Bob'), findsOneWidget);
  });

  testWidgets('Non-member sees active Join Club button and can join', (tester) async {
    final repo = FakeSocialRepo()..detailToReturn = sampleDetail;

    await tester.pumpWidget(createTestWidget(
      socialRepo: repo,
      currentUserId: 'non-member-user',
    ));
    await tester.pumpAndSettle();

    expect(find.text('Join Club'), findsOneWidget);
    expect(find.text('Member'), findsNothing);

    await tester.tap(find.text('Join Club'));
    await tester.pump();
    expect(repo.joinClubCalled, isTrue);
  });

  testWidgets('Existing member sees disabled Member button', (tester) async {
    final repo = FakeSocialRepo()..detailToReturn = sampleDetail;

    await tester.pumpWidget(createTestWidget(
      socialRepo: repo,
      currentUserId: 'existing-member-id',
    ));
    await tester.pumpAndSettle();

    expect(find.text('Member'), findsOneWidget);
    expect(find.text('Join Club'), findsNothing);
  });
}
