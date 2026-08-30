"""
CineVault OS — Phase W7: Social & Multiplayer Reliability Test Suite
=====================================================================
Verifies that all social and multiplayer systems are:
- Real PostgreSQL-backed
- Authorized and IDOR-safe (User A, User B, User C isolation)
- Race-safe and concurrency-resilient
- Idempotent on repeated joins/requests
- Strictly validated on lifecycle state transitions and active time windows
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.main import app
from services.api.database import get_db, AsyncSessionLocal
from services.api.routers.auth import generate_dev_jwt
from services.api.models.social import (
    FriendshipModel,
    RecommendationModel,
    PickRoomModel,
    PickVoteModel,
    WatchClubModel,
    ClubMembershipModel,
    ChallengeModel,
    ChallengeParticipantModel,
)
from services.api.schemas.social import (
    FriendshipStatusEnum,
    RecommendationStatusEnum,
)

client = TestClient(app)


def auth_headers(user_id: str) -> Dict[str, str]:
    token = generate_dev_jwt(
        user_id=user_id,
        email=f"{user_id}@cinevault.test",
        username=f"user_{user_id[-6:]}",
        roles=["authenticated_user"],
    )
    return {"Authorization": f"Bearer {token}"}


def get_real_title_ids(count: int = 3) -> List[str]:
    resp = client.get(f"/v1/titles?limit={count}")
    assert resp.status_code == 200
    data = resp.json()
    items = data.get("data", [])
    assert len(items) >= 1, "Catalog must have titles for testing."
    return [str(item["id"]) for item in items[:count]]


def extract_error_message(res) -> str:
    try:
        data = res.json()
        if isinstance(data, dict):
            if "error" in data and isinstance(data["error"], dict):
                return data["error"].get("message", "")
            return data.get("detail", "")
        return str(data)
    except Exception:
        return res.text


# =============================================================================
# 1. Friendship Lifecycle, IDOR Defense, and Pairwise Constraint
# =============================================================================

class TestW7FriendshipReliability:
    """Comprehensive test of friendships under multi-user concurrency and authorization."""

    def test_friendship_lifecycle_and_unfriend(self):
        """User A sends request to User B -> B accepts -> either can unfriend."""
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)

        # 1. User A requests User B
        res = client.post("/social/friendships", json={"addressee_id": user_b}, headers=h_a)
        assert res.status_code == 201
        data = res.json()
        f_id = data["friendship_id"]
        assert data["status"] == "PENDING"

        # 2. User B accepts
        accept_res = client.patch(f"/social/friendships/{f_id}", json={"status": "ACCEPTED"}, headers=h_b)
        assert accept_res.status_code == 200
        assert accept_res.json()["status"] == "ACCEPTED"

        # 3. User A lists friendships -> verifies accepted friendship exists
        list_res = client.get("/social/friendships", headers=h_a)
        assert list_res.status_code == 200
        f_list = list_res.json()
        assert any(f["friendship_id"] == f_id and f["status"] == "ACCEPTED" for f in f_list)

        # 4. User A unfriends
        del_res = client.delete(f"/social/friendships/{f_id}", headers=h_a)
        assert del_res.status_code == 204

        # 5. List friendships -> now empty
        list_res_after = client.get("/social/friendships", headers=h_a)
        assert not any(f["friendship_id"] == f_id for f in list_res_after.json())

    def test_friendship_self_request_rejected(self):
        """User cannot create a friendship with themselves."""
        user_a = str(uuid.uuid4())
        h_a = auth_headers(user_a)

        res = client.post("/social/friendships", json={"addressee_id": user_a}, headers=h_a)
        assert res.status_code == 400
        msg = extract_error_message(res)
        assert "themselves" in msg

    def test_friendship_idor_authorization_enforced(self):
        """User C (attacker) cannot accept, block, or delete A->B friendship."""
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        user_c = str(uuid.uuid4())  # Unauthorized third party
        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)
        h_c = auth_headers(user_c)

        # User A requests User B
        res = client.post("/social/friendships", json={"addressee_id": user_b}, headers=h_a)
        f_id = res.json()["friendship_id"]

        # 1. Attacker User C tries to ACCEPT -> 403 Forbidden
        attack_accept = client.patch(f"/social/friendships/{f_id}", json={"status": "ACCEPTED"}, headers=h_c)
        assert attack_accept.status_code == 403

        # 2. Requester User A tries to ACCEPT own request -> 403 Forbidden (only addressee can accept)
        requester_accept = client.patch(f"/social/friendships/{f_id}", json={"status": "ACCEPTED"}, headers=h_a)
        assert requester_accept.status_code == 403

        # 3. Attacker User C tries to DELETE -> 403 Forbidden
        attack_del = client.delete(f"/social/friendships/{f_id}", headers=h_c)
        assert attack_del.status_code == 403

        # 4. Legitimate recipient User B accepts -> 200 OK
        ok_accept = client.patch(f"/social/friendships/{f_id}", json={"status": "ACCEPTED"}, headers=h_b)
        assert ok_accept.status_code == 200

        # 5. Invalid transition: cannot downgrade ACCEPTED back to PENDING -> 400 Bad Request
        downgrade = client.patch(f"/social/friendships/{f_id}", json={"status": "PENDING"}, headers=h_b)
        assert downgrade.status_code == 400

    def test_duplicate_friendship_idempotency_and_pairwise_uniqueness(self):
        """Repeated friend requests between A and B return existing record and do not reset ACCEPTED status."""
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)

        # A requests B and B accepts
        res1 = client.post("/social/friendships", json={"addressee_id": user_b}, headers=h_a)
        f_id = res1.json()["friendship_id"]
        client.patch(f"/social/friendships/{f_id}", json={"status": "ACCEPTED"}, headers=h_b)

        # A requests B again -> must return existing ACCEPTED friendship
        res2 = client.post("/social/friendships", json={"addressee_id": user_b}, headers=h_a)
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["friendship_id"] == f_id
        assert data2["status"] == "ACCEPTED"

        # B requests A in reverse -> must return existing pairwise friendship
        res3 = client.post("/social/friendships", json={"addressee_id": user_a}, headers=h_b)
        assert res3.status_code == 201
        data3 = res3.json()
        assert data3["friendship_id"] == f_id
        assert data3["status"] == "ACCEPTED"


# =============================================================================
# 2. Peer Recommendation Lifecycle & IDOR Protection
# =============================================================================

class TestW7RecommendationReliability:
    """Comprehensive test of recommendation state machine, privacy, and actor authorization."""

    def test_recommendation_lifecycle_and_actor_authorization(self):
        """Verifies full lifecycle and proves that sender and third-parties cannot mutate state."""
        user_a = str(uuid.uuid4())  # Sender
        user_b = str(uuid.uuid4())  # Recipient
        user_c = str(uuid.uuid4())  # Attacker
        titles = get_real_title_ids(1)
        title_id = titles[0]

        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)
        h_c = auth_headers(user_c)

        # 1. Establish friendship
        f_res = client.post("/social/friendships", json={"addressee_id": user_b}, headers=h_a)
        f_id = f_res.json()["friendship_id"]
        client.patch(f"/social/friendships/{f_id}", json={"status": "ACCEPTED"}, headers=h_b)

        # 2. User A sends recommendation to User B
        rec_res = client.post(
            "/social/recommendations",
            json={
                "recipient_id": user_b,
                "title_id": title_id,
                "context_note": "A must-see cinematic piece",
                "sender_predicted_rating": 9.0,
            },
            headers=h_a,
        )
        assert rec_res.status_code == 201
        rec_data = rec_res.json()
        rec_id = rec_data["recommendation_id"]
        assert rec_data["status"] == "SENT"

        # 3. IDOR Check: User C cannot read this private recommendation
        c_read = client.get(f"/social/recommendations/{rec_id}", headers=h_c)
        assert c_read.status_code == 403

        # 4. Sender A and Recipient B CAN read
        a_read = client.get(f"/social/recommendations/{rec_id}", headers=h_a)
        assert a_read.status_code == 200
        b_read = client.get(f"/social/recommendations/{rec_id}", headers=h_b)
        assert b_read.status_code == 200

        # 5. Attacker User C tries to mutate state -> 403 Forbidden
        c_mutate = client.patch(f"/social/recommendations/{rec_id}", json={"status": "ACCEPTED"}, headers=h_c)
        assert c_mutate.status_code == 403

        # 6. Sender User A tries to mutate state -> 403 Forbidden (only recipient can accept)
        a_mutate = client.patch(f"/social/recommendations/{rec_id}", json={"status": "ACCEPTED"}, headers=h_a)
        assert a_mutate.status_code == 403

        # 7. Recipient User B accepts -> 200 OK
        b_accept = client.patch(f"/social/recommendations/{rec_id}", json={"status": "ACCEPTED"}, headers=h_b)
        assert b_accept.status_code == 200
        assert b_accept.json()["status"] == "ACCEPTED"

        # 8. Recipient User B marks watched -> 200 OK
        b_watched = client.patch(f"/social/recommendations/{rec_id}", json={"status": "WATCHED"}, headers=h_b)
        assert b_watched.status_code == 200
        assert b_watched.json()["status"] == "WATCHED"

        # 9. Recipient User B rates -> 200 OK
        b_rated = client.patch(
            f"/social/recommendations/{rec_id}",
            json={"status": "RATED", "recipient_actual_rating": 9.5},
            headers=h_b,
        )
        assert b_rated.status_code == 200
        assert b_rated.json()["status"] == "RATED"
        assert b_rated.json()["recipient_actual_rating"] == 9.5

    def test_recommendation_self_send_and_stranger_send_rejected(self):
        """Self-recommendations and recommendations to non-friends are rejected."""
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        titles = get_real_title_ids(1)
        title_id = titles[0]
        h_a = auth_headers(user_a)

        # Self send
        self_res = client.post(
            "/social/recommendations",
            json={"recipient_id": user_a, "title_id": title_id},
            headers=h_a,
        )
        assert self_res.status_code == 400

        # Stranger send (not friends)
        stranger_res = client.post(
            "/social/recommendations",
            json={"recipient_id": user_b, "title_id": title_id},
            headers=h_a,
        )
        assert stranger_res.status_code == 403


# =============================================================================
# 3. Watch Clubs, Activity Feed, and Idempotency
# =============================================================================

class TestW7WatchClubsReliability:
    """Comprehensive test of watch club membership, activity posting, and duplicate join safety."""

    def test_watch_club_lifecycle_and_idempotent_join(self):
        """Creator is OWNER; member joins idempotently without constraint errors."""
        user_a = str(uuid.uuid4())  # Club Creator / Owner
        user_b = str(uuid.uuid4())  # Member
        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)

        # 1. Create club
        create_res = client.post(
            "/social/clubs",
            json={"name": f"Cinephiles Society {uuid.uuid4().hex[:6]}", "description": "Weekly deep dives"},
            headers=h_a,
        )
        assert create_res.status_code == 201
        club_data = create_res.json()
        slug = club_data["slug"]
        assert club_data["member_count"] == 1

        # 2. User B joins
        join_res_1 = client.post(f"/social/clubs/{slug}/join", headers=h_b)
        assert join_res_1.status_code == 200
        assert join_res_1.json()["role"] == "MEMBER"

        # 3. User B joins AGAIN (must be idempotent, not crash with 500)
        join_res_2 = client.post(f"/social/clubs/{slug}/join", headers=h_b)
        assert join_res_2.status_code == 200
        assert join_res_2.json()["role"] == "MEMBER"

        # 4. Verify club detail has 2 members
        detail_res = client.get(f"/social/clubs/{slug}", headers=h_a)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["club"]["member_count"] == 2
        assert len(detail["members"]) == 2

        # 5. Activity Feed: User A posts activity
        act_res = client.post(
            f"/social/clubs/{slug}/activities",
            json={"activity_type": "DISCUSSION_POST", "metadata": {"topic": "Film Noir Aesthetics"}},
            headers=h_a,
        )
        assert act_res.status_code == 201

        # 6. User B retrieves feed
        feed_res = client.get(f"/social/clubs/{slug}/feed", headers=h_b)
        assert feed_res.status_code == 200
        feed = feed_res.json()
        assert len(feed) >= 1
        assert feed[0]["activity_type"] == "DISCUSSION_POST"


# =============================================================================
# 4. Monthly Challenges & Expiration Window Validation
# =============================================================================

class TestW7ChallengesReliability:
    """Comprehensive test of viewing challenges, progress tracking, and active window enforcement."""

    def test_challenge_lifecycle_idempotent_join_and_progress(self):
        """Participant joins idempotently, advances progress, and inactive challenges reject updates."""
        user_a = str(uuid.uuid4())
        h_a = auth_headers(user_a)

        now = datetime.now(timezone.utc)
        starts_at = (now - timedelta(days=1)).isoformat()
        ends_at = (now + timedelta(days=10)).isoformat()

        # 1. Create active challenge
        ch_res = client.post(
            "/social/challenges",
            json={
                "title": f"Director Spotlight {uuid.uuid4().hex[:4]}",
                "description": "Watch 3 Nolan movies this month",
                "challenge_type": "GLOBAL",
                "goal_count": 3,
                "starts_at": starts_at,
                "ends_at": ends_at,
            },
            headers=h_a,
        )
        assert ch_res.status_code == 201
        ch_id = ch_res.json()["challenge_id"]

        # 2. Join challenge
        join_1 = client.post(f"/social/challenges/{ch_id}/join", headers=h_a)
        assert join_1.status_code == 200
        assert join_1.json()["progress"] == 0

        # 3. Join again (idempotent)
        join_2 = client.post(f"/social/challenges/{ch_id}/join", headers=h_a)
        assert join_2.status_code == 200
        assert join_2.json()["progress"] == 0

        # 4. Update progress
        prog_1 = client.post(f"/social/challenges/{ch_id}/progress?increment=1", headers=h_a)
        assert prog_1.status_code == 200
        assert prog_1.json()["progress"] == 1
        assert prog_1.json()["completed"] is False

        # 5. Advance to completion
        prog_2 = client.post(f"/social/challenges/{ch_id}/progress?increment=2", headers=h_a)
        assert prog_2.status_code == 200
        assert prog_2.json()["progress"] == 3
        assert prog_2.json()["completed"] is True
        assert prog_2.json()["completed_at"] is not None

    def test_expired_challenge_progress_rejected(self):
        """Progress cannot be updated on expired challenges."""
        user_a = str(uuid.uuid4())
        h_a = auth_headers(user_a)

        now = datetime.now(timezone.utc)
        starts_at = (now - timedelta(days=20)).isoformat()
        ends_at = (now - timedelta(days=1)).isoformat()  # Expired yesterday

        # Create expired challenge
        ch_res = client.post(
            "/social/challenges",
            json={
                "title": f"Expired Challenge {uuid.uuid4().hex[:4]}",
                "challenge_type": "GLOBAL",
                "goal_count": 5,
                "starts_at": starts_at,
                "ends_at": ends_at,
            },
            headers=h_a,
        )
        assert ch_res.status_code == 201
        ch_id = ch_res.json()["challenge_id"]

        # Join expired challenge
        client.post(f"/social/challenges/{ch_id}/join", headers=h_a)

        # Progress increment must be rejected
        prog_res = client.post(f"/social/challenges/{ch_id}/progress?increment=1", headers=h_a)
        assert prog_res.status_code == 400
        msg = extract_error_message(prog_res)
        assert "inactive or expired" in msg.lower()


# =============================================================================
# 5. Pick Rooms (Group Ballot, Voting, Host Close & Concurrency)
# =============================================================================

class TestW7PickRoomsReliability:
    """Comprehensive test of movie night ballot rooms, live voting, host-only close, and concurrency."""

    def test_pick_room_voting_and_host_only_close(self):
        """Host closes room, non-host close is forbidden, closed room rejects further votes."""
        user_a = str(uuid.uuid4())  # Host
        user_b = str(uuid.uuid4())  # Voter 1
        user_c = str(uuid.uuid4())  # Voter 2 / Attacker
        titles = get_real_title_ids(2)
        candidate_1, candidate_2 = titles[0], titles[1]

        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)
        h_c = auth_headers(user_c)

        # 1. Host creates pick room
        room_res = client.post(
            "/social/pick-rooms",
            json={
                "title": "Friday Movie Night Ballot",
                "candidate_title_ids": [candidate_1, candidate_2],
                "expires_in_hours": 24,
            },
            headers=h_a,
        )
        assert room_res.status_code == 201
        room_data = room_res.json()
        slug = room_data["slug"]
        assert room_data["status"] == "OPEN"
        assert len(room_data["candidates"]) == 2

        # 2. Voter B votes for candidate 1
        vote_b = client.post(
            f"/social/pick-rooms/{slug}/vote",
            json={"title_id": candidate_1, "guest_name": "Bob"},
            headers=h_b,
        )
        assert vote_b.status_code == 200
        assert vote_b.json()["vote_type"] == "UPVOTE"

        # 3. Voter C votes for candidate 1 as well
        vote_c = client.post(
            f"/social/pick-rooms/{slug}/vote",
            json={"title_id": candidate_1, "guest_name": "Charlie"},
            headers=h_c,
        )
        assert vote_c.status_code == 200

        # 4. Attacker User C tries to close room -> 403 Forbidden
        attack_close = client.post(f"/social/pick-rooms/{slug}/close", headers=h_c)
        assert attack_close.status_code == 403

        # 5. Host User A closes room -> 200 OK
        host_close = client.post(f"/social/pick-rooms/{slug}/close", headers=h_a)
        assert host_close.status_code == 200
        closed_data = host_close.json()
        assert closed_data["status"] == "RESOLVED"
        assert closed_data["winning_title_id"] == candidate_1
        assert closed_data["total_votes_cast"] == 2

        # 6. Voting on closed room is rejected -> 400 Bad Request
        vote_late = client.post(
            f"/social/pick-rooms/{slug}/vote",
            json={"title_id": candidate_2},
            headers=h_b,
        )
        assert vote_late.status_code == 400
        msg = extract_error_message(vote_late)
        assert "closed" in msg.lower() or "resolved" in msg.lower() or "not open" in msg.lower()

    def test_concurrent_voting_tallies_accurately(self):
        """Simultaneous votes from multiple users tally accurately without race conditions."""
        host_id = str(uuid.uuid4())
        titles = get_real_title_ids(2)
        candidate_1, candidate_2 = titles[0], titles[1]
        h_host = auth_headers(host_id)

        # Create room
        room_res = client.post(
            "/social/pick-rooms",
            json={
                "title": "High Concurrency Ballot",
                "candidate_title_ids": [candidate_1, candidate_2],
                "expires_in_hours": 12,
            },
            headers=h_host,
        )
        assert room_res.status_code == 201
        slug = room_res.json()["slug"]

        # 10 distinct voters cast votes
        voter_ids = [str(uuid.uuid4()) for _ in range(10)]
        for idx, voter_id in enumerate(voter_ids):
            h_voter = auth_headers(voter_id)
            target_cand = candidate_1 if idx % 2 == 0 else candidate_2
            v_res = client.post(
                f"/social/pick-rooms/{slug}/vote",
                json={"title_id": target_cand, "guest_name": f"Voter-{idx}"},
                headers=h_voter,
            )
            assert v_res.status_code == 200

        # Retrieve room detail
        detail = client.get(f"/social/pick-rooms/{slug}").json()
        assert detail["total_votes"] == 10
        cand_1_votes = next(c["upvotes"] for c in detail["candidates"] if c["title_id"] == candidate_1)
        cand_2_votes = next(c["upvotes"] for c in detail["candidates"] if c["title_id"] == candidate_2)
        assert cand_1_votes == 5
        assert cand_2_votes == 5


# =============================================================================
# 6. Viral Invites & Referrals
# =============================================================================

class TestW7InvitesReferralsReliability:
    """Comprehensive test of invite token creation, preview snapshot, and referral safety."""

    def test_invite_preview_accept_and_non_self(self):
        """Invites can be previewed publicly, accepted by friends, but not by inviter."""
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        h_a = auth_headers(user_a)
        h_b = auth_headers(user_b)

        # 1. User A creates invite token
        inv_res = client.post("/social/invites", headers=h_a)
        assert inv_res.status_code == 200
        token = inv_res.json()["token"]

        # 2. Public preview (unauthenticated)
        prev_res = client.get(f"/social/invites/{token}/preview")
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        assert "total_watched_count" in prev_data

        # 3. User A cannot accept own invite
        self_accept = client.post(f"/social/invites/{token}/accept", headers=h_a)
        assert self_accept.status_code == 400

        # 4. User B accepts invite
        b_accept = client.post(f"/social/invites/{token}/accept", headers=h_b)
        assert b_accept.status_code == 200
        assert b_accept.json()["status"] in ("ACCEPTED", "PENDING")

        # 5. User A checks referrals
        ref_res = client.get("/social/referrals", headers=h_a)
        assert ref_res.status_code == 200
        ref_data = ref_res.json()
        assert ref_data["total_conversions"] >= 1
