// CineVault OS — InviteScreen Widget Tests

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cinevault_client/core/theme/app_theme.dart';
import 'package:cinevault_client/domain/entities/social.dart';
import 'package:cinevault_client/domain/repositories/social_repository.dart';
import 'package:cinevault_client/presentation/providers/social_provider.dart';
import 'package:cinevault_client/presentation/screens/invite_screen.dart';

class FakeSocialRepo implements SocialRepository {
  bool createInviteCalled = false;

  @override
  Future<InviteTokenEntity> createInviteToken() async {
    createInviteCalled = true;
    return const InviteTokenEntity(
      token: 'tok-abc-123',
      inviteUrl: 'https://cinevault.org/invite/tok-abc-123',
      inviterId: 'user-1',
      inviterName: 'Tester',
      createdAt: '2026-09-09T00:00:00Z',
    );
  }

  @override
  Future<ReferralStatsEntity> getReferralStats() async {
    return const ReferralStatsEntity(
      inviterId: 'user-1',
      totalInvitesSent: 8,
      totalConversions: 5,
      qualifiedReferrals: 3,
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  testWidgets('Renders Invite screen, referral stats, and generates invite token', (tester) async {
    final repo = FakeSocialRepo();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          socialRepositoryProvider.overrideWithValue(repo),
        ],
        child: MaterialApp(
          theme: AppTheme.darkTheme,
          home: const InviteScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify header & referral stats
    expect(find.text('Invite a Friend'), findsNWidgets(2)); // AppBar + card title
    expect(find.text('Your Referral Stats'), findsOneWidget);
    expect(find.text('8'), findsOneWidget); // totalInvitesSent
    expect(find.text('5'), findsOneWidget); // totalConversions
    expect(find.text('3'), findsOneWidget); // qualifiedReferrals

    // Verify Generate button
    final generateBtn = find.text('Generate Invite Link');
    expect(generateBtn, findsOneWidget);

    await tester.tap(generateBtn);
    await tester.pumpAndSettle();

    expect(repo.createInviteCalled, isTrue);
    expect(find.text('https://cinevault.org/invite/tok-abc-123'), findsOneWidget);
  });
}
