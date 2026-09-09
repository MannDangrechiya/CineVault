// CineVault OS — PickRoomScreen Widget & Host Gating Tests

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
import 'package:cinevault_client/presentation/screens/pick_room_screen.dart';

class FakeSocialRepository implements SocialRepository {
  PickRoomEntity? roomToReturn;
  String? lastVotedTitleId;
  bool closeVotingCalled = false;

  @override
  Future<PickRoomEntity> getPickRoom(String slug) async {
    if (roomToReturn != null) return roomToReturn!;
    throw Exception('Room not found');
  }

  @override
  Future<PickVoteEntity> castPickVote({
    required String slug,
    required String titleId,
    String voteType = 'UPVOTE',
  }) async {
    lastVotedTitleId = titleId;
    return PickVoteEntity(
      voteId: 'vote-1',
      roomId: 'room-1',
      titleId: titleId,
      voterName: 'Test Voter',
      voteType: voteType,
    );
  }

  @override
  Future<PickRoomEntity> closePickRoom(String slug) async {
    closeVotingCalled = true;
    return PickRoomEntity(
      roomId: roomToReturn!.roomId,
      hostId: roomToReturn!.hostId,
      hostName: roomToReturn!.hostName,
      slug: roomToReturn!.slug,
      title: roomToReturn!.title,
      status: 'RESOLVED',
      totalVotes: roomToReturn!.totalVotes,
      candidates: roomToReturn!.candidates,
      createdAt: roomToReturn!.createdAt,
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
      accessToken: 'test-token',
      refreshToken: 'test-refresh',
      userId: userId!,
      email: 'user@cinevault.org',
      roles: const ['AuthenticatedUser'],
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  const sampleRoom = PickRoomEntity(
    roomId: 'room-1',
    slug: 'movie-night-2026',
    title: 'Friday Movie Night',
    hostId: 'host-user-id',
    hostName: 'Alice',
    status: 'OPEN',
    totalVotes: 5,
    candidates: [
      CandidateSummaryEntity(
        titleId: 'title-1',
        canonicalTitle: 'Inception',
        productionYear: 2010,
        upvotes: 3,
      ),
      CandidateSummaryEntity(
        titleId: 'title-2',
        canonicalTitle: 'Interstellar',
        productionYear: 2014,
        upvotes: 2,
      ),
    ],
    createdAt: '2026-09-09T00:00:00Z',
  );

  Widget createTestWidget({
    required FakeSocialRepository socialRepo,
    required String? currentUserId,
  }) {
    return ProviderScope(
      overrides: [
        socialRepositoryProvider.overrideWithValue(socialRepo),
        authProvider.overrideWith((ref) => AuthNotifier(FakeAuthRepo(currentUserId))),
      ],
      child: MaterialApp(
        theme: AppTheme.darkTheme,
        home: const PickRoomScreen(slug: 'movie-night-2026'),
      ),
    );
  }

  testWidgets('PickRoomScreen displays room title, candidates, and upvote percentages', (tester) async {
    final fakeRepo = FakeSocialRepository()..roomToReturn = sampleRoom;

    await tester.pumpWidget(createTestWidget(
      socialRepo: fakeRepo,
      currentUserId: 'non-host-viewer',
    ));
    await tester.pumpAndSettle();

    expect(find.text('Friday Movie Night'), findsOneWidget);
    expect(find.text('Hosted by Alice'), findsOneWidget);
    expect(find.text('OPEN'), findsOneWidget);
    expect(find.text('Inception'), findsOneWidget);
    expect(find.text('Interstellar'), findsOneWidget);
    expect(find.textContaining('60%'), findsOneWidget);
    expect(find.textContaining('40%'), findsOneWidget);
  });

  testWidgets('Non-host viewer does NOT see Close Voting button', (tester) async {
    final fakeRepo = FakeSocialRepository()..roomToReturn = sampleRoom;

    await tester.pumpWidget(createTestWidget(
      socialRepo: fakeRepo,
      currentUserId: 'different-viewer',
    ));
    await tester.pumpAndSettle();

    expect(find.text('Close Voting'), findsNothing);
  });

  testWidgets('Room host sees Close Voting button and can close voting', (tester) async {
    final fakeRepo = FakeSocialRepository()..roomToReturn = sampleRoom;

    await tester.pumpWidget(createTestWidget(
      socialRepo: fakeRepo,
      currentUserId: 'host-user-id',
    ));
    await tester.pumpAndSettle();

    expect(find.text('Close Voting'), findsOneWidget);

    await tester.tap(find.text('Close Voting'));
    await tester.pump();
    expect(fakeRepo.closeVotingCalled, isTrue);
  });

  testWidgets('Casting an upvote calls repository castPickVote', (tester) async {
    final fakeRepo = FakeSocialRepository()..roomToReturn = sampleRoom;

    await tester.pumpWidget(createTestWidget(
      socialRepo: fakeRepo,
      currentUserId: 'some-user',
    ));
    await tester.pumpAndSettle();

    final upvoteButtons = find.byIcon(Icons.thumb_up_outlined);
    expect(upvoteButtons, findsNWidgets(2));
    await tester.tap(upvoteButtons.first);
    await tester.pump();

    expect(fakeRepo.lastVotedTitleId, 'title-1');
  });
}
