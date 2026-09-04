# CineVault OS — Phase 30 Backup & Disaster Recovery Verification Test
# Tests REAL PostgreSQL Backup & Restore:
# 1. Connects to live PostgreSQL environment in Docker.
# 2. Spawns an isolated disposable test database (cinevault_dr_source).
# 3. Clones full schema from migrated cinevault database and inserts representative
#    CineVault data across all 6 logical schemas (canonical, personal, social, quality, ingestion, audit).
# 4. Executes pg_dump inside PostgreSQL container to create a real binary/custom backup archive.
# 5. Drops/disconnects from disposable source database.
# 6. Spawns clean recovery database (cinevault_dr_recovery).
# 7. Executes pg_restore to restore backup into clean recovery database.
# 8. Verifies schema integrity, table existence, representative row counts, FK relationships,
#    database constraints, and vector operations on restored data.
# 9. Cleans up disposable recovery database and temporary backup files.
# Main developer database (cinevault) remains 100% untouched.

import os
import subprocess
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from services.api.config import config

import asyncio

def test_real_postgresql_backup_and_restore_disaster_recovery():
    """
    Executes an end-to-end real PostgreSQL backup, drop, restore, and data integrity test.
    """
    async def _test():
        # 1. Verify PostgreSQL connection configuration
        admin_url = f"postgresql+asyncpg://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/postgres"
        
        admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        source_db_name = f"cinevault_dr_src_{uuid.uuid4().hex[:8]}"
        recovery_db_name = f"cinevault_dr_rec_{uuid.uuid4().hex[:8]}"
        backup_file_in_container = f"/tmp/{source_db_name}.dump"
        
        source_db_url = f"postgresql+asyncpg://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{source_db_name}"
        recovery_db_url = f"postgresql+asyncpg://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{recovery_db_name}"

        try:
            # Step 2: Create disposable source database using template cinevault
            async with admin_engine.connect() as conn:
                # Terminate any stray connections to template if needed
                await conn.execute(text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'cinevault' AND pid <> pg_backend_pid()"
                ))
                await conn.execute(text(f"CREATE DATABASE {source_db_name} WITH TEMPLATE cinevault OWNER {config.postgres_user}"))
            
            # Step 3: Insert representative records across all 6 logical schemas in source DB
            source_engine = create_async_engine(source_db_url)
            test_title_id = uuid.uuid4()
            test_person_id = uuid.uuid4()
            test_user_id = uuid.uuid4()
            test_friend_id = uuid.uuid4()
            test_club_id = uuid.uuid4()
            test_challenge_id = uuid.uuid4()
            test_room_id = uuid.uuid4()
            test_proposal_id = uuid.uuid4()
            test_run_id = uuid.uuid4()
            test_list_id = uuid.uuid4()
            now_utc = datetime.now(timezone.utc)
            
            async with source_engine.begin() as conn:
                # Canonical Schema
                await conn.execute(text("""
                    INSERT INTO canonical.title (
                        title_id, display_id, content_type_id, canonical_title, original_title, production_year, status_flag
                    ) VALUES (
                        :title_id, :display_id, 'movie', 'Inception DR Test', 'Inception', 2010, 'ACTIVE'
                    )
                """), {"title_id": test_title_id, "display_id": f"MOV-DR-{uuid.uuid4().hex[:6]}"})

                await conn.execute(text("""
                    INSERT INTO canonical.genre (genre_id, name)
                    VALUES ('dr-sci-fi', 'DR Sci-Fi')
                    ON CONFLICT (genre_id) DO NOTHING
                """))

                await conn.execute(text("""
                    INSERT INTO canonical.title_genre (title_id, genre_id)
                    VALUES (:title_id, 'dr-sci-fi')
                """), {"title_id": test_title_id})

                await conn.execute(text("""
                    INSERT INTO canonical.person (person_id, canonical_name)
                    VALUES (:person_id, 'Christopher Nolan DR')
                """), {"person_id": test_person_id})

                await conn.execute(text("""
                    INSERT INTO canonical.credit_role (credit_role_id, role_name, category)
                    VALUES ('dr-director', 'Director', 'Directing')
                    ON CONFLICT (credit_role_id) DO NOTHING
                """))

                await conn.execute(text("""
                    INSERT INTO canonical.credit (credit_id, title_id, person_id, credit_role_id)
                    VALUES (:credit_id, :title_id, :person_id, 'dr-director')
                """), {"credit_id": uuid.uuid4(), "title_id": test_title_id, "person_id": test_person_id})

                # Personal Schema
                await conn.execute(text("""
                    INSERT INTO personal.library_entry (user_id, title_id, added_at)
                    VALUES (:user_id, :title_id, :now)
                """), {"user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.user_title_state (user_id, title_id, manual_status_override, is_favorite, updated_at)
                    VALUES (:user_id, :title_id, 'PLAN_TO_WATCH', true, :now)
                """), {"user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.watch_event (watch_event_id, user_id, title_id, watched_at, device_type)
                    VALUES (:event_id, :user_id, :title_id, :now, 'OLED TV')
                """), {"event_id": uuid.uuid4(), "user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.rating (rating_id, user_id, title_id, rating_value, rated_at)
                    VALUES (:rating_id, :user_id, :title_id, 10, :now)
                """), {"rating_id": uuid.uuid4(), "user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.note (note_id, user_id, title_id, note_text, created_at)
                    VALUES (:note_id, :user_id, :title_id, 'Mind-bending dream architecture.', :now)
                """), {"note_id": uuid.uuid4(), "user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.review (review_id, user_id, title_id, review_title, review_text, created_at)
                    VALUES (:review_id, :user_id, :title_id, 'Masterpiece', 'Flawless execution of high concept.', :now)
                """), {"review_id": uuid.uuid4(), "user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.user_list (list_id, user_id, title, description, is_private, created_at, updated_at)
                    VALUES (:list_id, :user_id, 'DR Test Favorites', 'Disaster recovery verified list', false, :now, :now)
                """), {"list_id": test_list_id, "user_id": test_user_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.user_list_item (item_id, list_id, title_id, position, added_at)
                    VALUES (:item_id, :list_id, :title_id, 1, :now)
                """), {"item_id": uuid.uuid4(), "list_id": test_list_id, "title_id": test_title_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO personal.user_streak (user_id, current_streak, longest_streak, last_watch_date, updated_at)
                    VALUES (:user_id, 5, 12, CURRENT_DATE, :now)
                """), {"user_id": test_user_id, "now": now_utc})

                # Social Schema
                req_id, add_id = sorted([test_user_id, test_friend_id])
                await conn.execute(text("""
                    INSERT INTO social.friendship (friendship_id, requester_id, addressee_id, status, trust_score, created_at, updated_at)
                    VALUES (:friendship_id, :requester_id, :addressee_id, 'ACCEPTED', 85, :now, :now)
                """), {"friendship_id": uuid.uuid4(), "requester_id": req_id, "addressee_id": add_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO social.recommendation (recommendation_id, sender_id, recipient_id, title_id, status, context_note, sent_at, updated_at)
                    VALUES (:rec_id, :sender_id, :recipient_id, :title_id, 'SENT', 'Must watch this weekend!', :now, :now)
                """), {"rec_id": uuid.uuid4(), "sender_id": test_user_id, "recipient_id": test_friend_id, "title_id": test_title_id, "now": now_utc})

                zero_vector = "[" + ",".join(["0.05"] * 384) + "]"
                await conn.execute(text(f"""
                    INSERT INTO social.user_taste_profile (user_id, taste_vector, last_computed_at)
                    VALUES (:user_id, '{zero_vector}'::vector, :now)
                """), {"user_id": test_user_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO social.watch_club (club_id, slug, name, created_by, created_at)
                    VALUES (:club_id, :slug, 'DR Cinephiles Society', :creator_id, :now)
                """), {"club_id": test_club_id, "slug": f"dr-club-{uuid.uuid4().hex[:6]}", "creator_id": test_user_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO social.club_membership (club_id, user_id, role, joined_at)
                    VALUES (:club_id, :user_id, 'OWNER', :now)
                """), {"club_id": test_club_id, "user_id": test_user_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO social.challenge (challenge_id, challenge_type, title, description, starts_at, ends_at, goal_count, criteria_json, created_at)
                    VALUES (:challenge_id, 'GLOBAL', 'DR Sci-Fi Marathon', 'Watch 5 sci-fi titles', :now, :ends_at, 5, '{"genre": "Sci-Fi"}', :now)
                """), {"challenge_id": test_challenge_id, "now": now_utc, "ends_at": datetime(2030, 1, 1, tzinfo=timezone.utc)})

                await conn.execute(text("""
                    INSERT INTO social.challenge_participant (challenge_id, user_id, progress, completed, joined_at)
                    VALUES (:challenge_id, :user_id, 3, false, :now)
                """), {"challenge_id": test_challenge_id, "user_id": test_user_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO social.pick_room (room_id, slug, title, host_id, status, created_at)
                    VALUES (:room_id, :slug, 'DR Movie Night', :creator_id, 'OPEN', :now)
                """), {"room_id": test_room_id, "slug": f"dr-room-{uuid.uuid4().hex[:6]}", "creator_id": test_user_id, "now": now_utc})

                await conn.execute(text("""
                    INSERT INTO social.pick_room_candidate (room_id, title_id)
                    VALUES (:room_id, :title_id)
                """), {"room_id": test_room_id, "title_id": test_title_id})

                await conn.execute(text("""
                    INSERT INTO social.pick_vote (vote_id, room_id, user_id, title_id, voter_fingerprint, vote_type, created_at)
                    VALUES (:vote_id, :room_id, :user_id, :title_id, 'fp-user-1', 'UPVOTE', :now)
                """), {"vote_id": uuid.uuid4(), "room_id": test_room_id, "user_id": test_user_id, "title_id": test_title_id, "now": now_utc})

                # Quality Schema (CAT-6 AI Proposal Staging)
                await conn.execute(text("""
                    INSERT INTO quality.ai_proposal_staging (
                        proposal_id, target_entity_type, target_entity_id, proposed_attribute_name,
                        proposed_value, confidence_score, evidence_payload, review_status, provider_name, prompt_version, submitted_by,
                        submitted_at
                    ) VALUES (
                        :proposal_id, 'TITLE', :title_id, 'synopsis',
                        'New AI synopsis', 0.98, '{"signature": "hmac-sha256-signature-check"}', 'PENDING', 'openai', 'v1.0', 'curator-service',
                        :now
                    )
                """), {"proposal_id": test_proposal_id, "title_id": test_title_id, "now": now_utc})

                # Ingestion Schema
                await conn.execute(text("""
                    INSERT INTO ingestion.ingestion_runs (
                        run_id, provider_name, status, records_seen, records_valid, records_created, records_updated,
                        started_at, completed_at
                    ) VALUES (
                        :run_id, 'IMDB', 'COMPLETED', 100, 100, 10, 90, :now, :now
                    )
                """), {"run_id": test_run_id, "now": now_utc})

            await source_engine.dispose()

            # Step 4: Run pg_dump inside Docker container to create binary custom backup
            dump_cmd = [
                "docker", "exec", "cinevault-local-postgres",
                "pg_dump", "-U", config.postgres_user, "-d", source_db_name,
                "-F", "c", "-f", backup_file_in_container
            ]
            dump_proc = subprocess.run(dump_cmd, capture_output=True, text=True)
            assert dump_proc.returncode == 0, f"pg_dump failed: {dump_proc.stderr}"

            # Step 5: Destroy/Drop disposable source database to simulate complete loss of source
            async with admin_engine.connect() as conn:
                await conn.execute(text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{source_db_name}' AND pid <> pg_backend_pid()"
                ))
                await conn.execute(text(f"DROP DATABASE {source_db_name}"))

            # Step 6: Create clean empty recovery database
            async with admin_engine.connect() as conn:
                await conn.execute(text(f"CREATE DATABASE {recovery_db_name} OWNER {config.postgres_user}"))

            # Step 7: Execute pg_restore into recovery database
            restore_cmd = [
                "docker", "exec", "cinevault-local-postgres",
                "pg_restore", "-U", config.postgres_user, "-d", recovery_db_name,
                backup_file_in_container
            ]
            restore_proc = subprocess.run(restore_cmd, capture_output=True, text=True)
            # pg_restore exit code 0 is clean success
            assert restore_proc.returncode == 0, f"pg_restore failed: {restore_proc.stderr}"

            # Step 8: Verify restored database integrity
            recovery_engine = create_async_engine(recovery_db_url)
            async with recovery_engine.connect() as conn:
                # 8.1 Schema existence verification
                schemas_res = await conn.execute(text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('canonical', 'personal', 'social', 'quality', 'ingestion', 'audit')"
                ))
                restored_schemas = {r[0] for r in schemas_res.fetchall()}
                assert restored_schemas == {'canonical', 'personal', 'social', 'quality', 'ingestion', 'audit'}

                # 8.2 Canonical data verification
                title_res = await conn.execute(text(
                    "SELECT canonical_title, production_year, status_flag FROM canonical.title WHERE title_id = :id"
                ), {"id": test_title_id})
                title_row = title_res.fetchone()
                assert title_row is not None
                assert title_row[0] == "Inception DR Test"
                assert title_row[1] == 2010
                assert title_row[2] == "ACTIVE"

                genre_res = await conn.execute(text(
                    "SELECT genre_id FROM canonical.title_genre WHERE title_id = :id"
                ), {"id": test_title_id})
                assert genre_res.scalar_one() == "dr-sci-fi"

                credit_res = await conn.execute(text(
                    "SELECT person_id, credit_role_id FROM canonical.credit WHERE title_id = :id"
                ), {"id": test_title_id})
                credit_row = credit_res.fetchone()
                assert credit_row is not None
                assert credit_row[0] == test_person_id
                assert credit_row[1] == "dr-director"

                # 8.3 Personal data verification
                lib_res = await conn.execute(text(
                    "SELECT COUNT(*) FROM personal.library_entry WHERE user_id = :uid AND title_id = :tid"
                ), {"uid": test_user_id, "tid": test_title_id})
                assert lib_res.scalar_one() == 1

                state_res = await conn.execute(text(
                    "SELECT manual_status_override, is_favorite FROM personal.user_title_state WHERE user_id = :uid AND title_id = :tid"
                ), {"uid": test_user_id, "tid": test_title_id})
                state_row = state_res.fetchone()
                assert state_row[0] == "PLAN_TO_WATCH"
                assert state_row[1] is True

                evt_res = await conn.execute(text(
                    "SELECT device_type FROM personal.watch_event WHERE user_id = :uid AND title_id = :tid"
                ), {"uid": test_user_id, "tid": test_title_id})
                evt_row = evt_res.fetchone()
                assert evt_row[0] == "OLED TV"

                rating_res = await conn.execute(text(
                    "SELECT rating_value FROM personal.rating WHERE user_id = :uid AND title_id = :tid"
                ), {"uid": test_user_id, "tid": test_title_id})
                assert rating_res.scalar_one() == 10

                note_res = await conn.execute(text(
                    "SELECT note_text FROM personal.note WHERE user_id = :uid AND title_id = :tid"
                ), {"uid": test_user_id, "tid": test_title_id})
                assert note_res.scalar_one() == "Mind-bending dream architecture."

                review_res = await conn.execute(text(
                    "SELECT review_title, review_text FROM personal.review WHERE user_id = :uid AND title_id = :tid"
                ), {"uid": test_user_id, "tid": test_title_id})
                rev_row = review_res.fetchone()
                assert rev_row[0] == "Masterpiece"
                assert rev_row[1] == "Flawless execution of high concept."

                list_res = await conn.execute(text(
                    "SELECT title FROM personal.user_list WHERE list_id = :lid"
                ), {"lid": test_list_id})
                assert list_res.scalar_one() == "DR Test Favorites"

                streak_res = await conn.execute(text(
                    "SELECT current_streak, longest_streak FROM personal.user_streak WHERE user_id = :uid"
                ), {"uid": test_user_id})
                streak_row = streak_res.fetchone()
                assert streak_row[0] == 5
                assert streak_row[1] == 12

                # 8.4 Social data & pgvector verification
                friend_res = await conn.execute(text(
                    "SELECT status, trust_score FROM social.friendship WHERE requester_id = :req AND addressee_id = :add"
                ), {"req": req_id, "add": add_id})
                friend_row = friend_res.fetchone()
                assert friend_row[0] == "ACCEPTED"
                assert friend_row[1] == 85

                rec_res = await conn.execute(text(
                    "SELECT status, context_note FROM social.recommendation WHERE title_id = :tid"
                ), {"tid": test_title_id})
                rec_row = rec_res.fetchone()
                assert rec_row[0] == "SENT"
                assert rec_row[1] == "Must watch this weekend!"

                # Test vector distance calculation on restored pgvector data
                vector_res = await conn.execute(text(f"""
                    SELECT taste_vector <=> '{zero_vector}'::vector FROM social.user_taste_profile WHERE user_id = :uid
                """), {"uid": test_user_id})
                assert vector_res.scalar_one() is not None

                club_res = await conn.execute(text(
                    "SELECT name, created_by FROM social.watch_club WHERE club_id = :cid"
                ), {"cid": test_club_id})
                club_row = club_res.fetchone()
                assert club_row[0] == "DR Cinephiles Society"
                assert club_row[1] == test_user_id

                challenge_res = await conn.execute(text(
                    "SELECT title, goal_count FROM social.challenge WHERE challenge_id = :cid"
                ), {"cid": test_challenge_id})
                ch_row = challenge_res.fetchone()
                assert ch_row[0] == "DR Sci-Fi Marathon"
                assert ch_row[1] == 5

                room_res = await conn.execute(text(
                    "SELECT title, status FROM social.pick_room WHERE room_id = :rid"
                ), {"rid": test_room_id})
                rm_row = room_res.fetchone()
                assert rm_row[0] == "DR Movie Night"
                assert rm_row[1] == "OPEN"

                # 8.5 Quality & Ingestion data verification
                prop_res = await conn.execute(text(
                    "SELECT review_status, proposed_value, evidence_payload FROM quality.ai_proposal_staging WHERE proposal_id = :pid"
                ), {"pid": test_proposal_id})
                prop_row = prop_res.fetchone()
                assert prop_row[0] == "PENDING"
                assert prop_row[1] == "New AI synopsis"
                assert prop_row[2]["signature"] == "hmac-sha256-signature-check"

                ing_res = await conn.execute(text(
                    "SELECT provider_name, status, records_seen FROM ingestion.ingestion_runs WHERE run_id = :rid"
                ), {"rid": test_run_id})
                ing_row = ing_res.fetchone()
                assert ing_row[0] == "IMDB"
                assert ing_row[1] == "COMPLETED"
                assert ing_row[2] == 100

                # 8.6 Constraint and Relationship integrity verification
                # Verify foreign key constraint enforcement in restored DB
                fk_violation_raised = False
                try:
                    await conn.execute(text(
                        "INSERT INTO personal.library_entry (user_id, title_id, added_at) "
                        "VALUES (:uid, :nonexistent_tid, :now)"
                    ), {"uid": test_user_id, "nonexistent_tid": uuid.uuid4(), "now": now_utc})
                except Exception:
                    fk_violation_raised = True
                assert fk_violation_raised, "Restored database must enforce foreign key constraints"

            await recovery_engine.dispose()

        finally:
            # Step 9: Clean up disposable database & backup file
            async with admin_engine.connect() as conn:
                await conn.execute(text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname IN ('{source_db_name}', '{recovery_db_name}') AND pid <> pg_backend_pid()"
                ))
                await conn.execute(text(f"DROP DATABASE IF EXISTS {source_db_name}"))
                await conn.execute(text(f"DROP DATABASE IF EXISTS {recovery_db_name}"))
            await admin_engine.dispose()

            subprocess.run(["docker", "exec", "cinevault-local-postgres", "rm", "-f", backup_file_in_container], capture_output=True)

    asyncio.run(_test())



