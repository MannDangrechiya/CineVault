import asyncio
import asyncpg
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api.config import config

async def run_integrity_audit():
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST") or "localhost",
        port=int(os.getenv("POSTGRES_PORT") or 5432),
        user=config.postgres_user,
        password=config.postgres_password,
        database=config.postgres_db
    )
    
    results = {}
    
    # 1. Catalog count
    results["total_canonical_titles"] = await conn.fetchval("SELECT count(*) FROM canonical.title;")
    results["total_editions"] = await conn.fetchval("SELECT count(*) FROM canonical.edition;")
    results["total_seasons"] = await conn.fetchval("SELECT count(*) FROM canonical.season;")
    results["total_episodes"] = await conn.fetchval("SELECT count(*) FROM canonical.episode;")
    
    # 2. Duplicate external IDs
    results["duplicate_external_ids"] = await conn.fetchval("""
        SELECT count(*) FROM (
            SELECT provider_name, external_id, count(*)
            FROM canonical.title_external_id
            GROUP BY provider_name, external_id
            HAVING count(*) > 1
        ) sub;
    """)
    
    # 3. Duplicate display IDs
    results["duplicate_display_ids"] = await conn.fetchval("""
        SELECT count(*) FROM (
            SELECT display_id, count(*)
            FROM canonical.title
            GROUP BY display_id
            HAVING count(*) > 1
        ) sub;
    """)
    
    # 4. Orphan seasons or episodes
    results["orphan_seasons"] = await conn.fetchval("""
        SELECT count(*) FROM canonical.season s
        LEFT JOIN canonical.title t ON s.title_id = t.title_id
        WHERE t.title_id IS NULL;
    """)
    results["orphan_episodes"] = await conn.fetchval("""
        SELECT count(*) FROM canonical.episode e
        LEFT JOIN canonical.season s ON e.season_id = s.season_id
        WHERE s.season_id IS NULL;
    """)
    
    # 5. Orphan editions
    results["orphan_editions"] = await conn.fetchval("""
        SELECT count(*) FROM canonical.edition ed
        LEFT JOIN canonical.title t ON ed.title_id = t.title_id
        WHERE t.title_id IS NULL;
    """)

    # 6. Orphan personal data references
    results["orphan_watch_events"] = await conn.fetchval("""
        SELECT count(*) FROM personal.watch_event we
        LEFT JOIN canonical.title t ON we.title_id = t.title_id
        WHERE we.title_id IS NOT NULL AND t.title_id IS NULL;
    """)
    results["orphan_ratings"] = await conn.fetchval("""
        SELECT count(*) FROM personal.rating r
        LEFT JOIN canonical.title t ON r.title_id = t.title_id
        WHERE t.title_id IS NULL;
    """)
    results["orphan_notes"] = await conn.fetchval("""
        SELECT count(*) FROM personal.note n
        LEFT JOIN canonical.title t ON n.title_id = t.title_id
        WHERE t.title_id IS NULL;
    """)
    results["orphan_reviews"] = await conn.fetchval("""
        SELECT count(*) FROM personal.review rev
        LEFT JOIN canonical.title t ON rev.title_id = t.title_id
        WHERE t.title_id IS NULL;
    """)
    results["orphan_list_items"] = await conn.fetchval("""
        SELECT count(*) FROM personal.user_list_item li
        LEFT JOIN canonical.title t ON li.title_id = t.title_id
        WHERE t.title_id IS NULL;
    """)
    
    # 7. Duplicate friendships (pairwise LEAST/GREATEST)
    results["duplicate_pairwise_friendships"] = await conn.fetchval("""
        SELECT count(*) FROM (
            SELECT LEAST(requester_id, addressee_id), GREATEST(requester_id, addressee_id), count(*)
            FROM social.friendship
            GROUP BY LEAST(requester_id, addressee_id), GREATEST(requester_id, addressee_id)
            HAVING count(*) > 1
        ) sub;
    """)
    
    # 8. Duplicate pick-room votes
    results["duplicate_pick_votes"] = await conn.fetchval("""
        SELECT count(*) FROM (
            SELECT room_id, voter_fingerprint, title_id, count(*)
            FROM social.pick_vote
            GROUP BY room_id, voter_fingerprint, title_id
            HAVING count(*) > 1
        ) sub;
    """)
    
    # 9. Duplicate list items
    results["duplicate_list_items"] = await conn.fetchval("""
        SELECT count(*) FROM (
            SELECT list_id, title_id, count(*)
            FROM personal.user_list_item
            GROUP BY list_id, title_id
            HAVING count(*) > 1
        ) sub;
    """)

    # 10. Duplicate club memberships
    results["duplicate_club_memberships"] = await conn.fetchval("""
        SELECT count(*) FROM (
            SELECT club_id, user_id, count(*)
            FROM social.club_membership
            GROUP BY club_id, user_id
            HAVING count(*) > 1
        ) sub;
    """)

    # 11. Provenance and audit records
    results["provenance_records_count"] = await conn.fetchval("SELECT count(*) FROM quality.field_provenance;")
    results["audit_logs_count"] = await conn.fetchval("SELECT count(*) FROM audit.canonical_audit_log;")
    results["quarantine_records_count"] = await conn.fetchval("SELECT count(*) FROM quality.quarantine_record;")
    results["metadata_conflicts_count"] = await conn.fetchval("SELECT count(*) FROM quality.metadata_conflict;")
    
    # 12. Invalid challenge participation
    results["invalid_challenge_participants"] = await conn.fetchval("""
        SELECT count(*) FROM social.challenge_participant cp
        LEFT JOIN social.challenge c ON cp.challenge_id = c.challenge_id
        WHERE c.challenge_id IS NULL;
    """)
    
    await conn.close()
    
    print("=== DATABASE INTEGRITY AUDIT RESULTS ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run_integrity_audit())
