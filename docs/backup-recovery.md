# CineVault OS — Backup & Disaster Recovery Architecture (Phase 30 / W11)

## 1. Overview & Disaster Recovery Invariants
CineVault enforces an automated backup and disaster recovery validation workflow to guarantee data integrity across all 6 logical PostgreSQL schemas:
1. \canonical\ (CAT-1 Catalog, Titles, Editions, Releases, Credits, Genres, Streaming Offers)
2. \personal\ (CAT-2 User Media Library, Watch Events, Ratings, Notes, Reviews, Collections, Streaks)
3. \social\ (Friendships, Recommendations, pgvector 384-d Taste Profiles, Watch Clubs, Challenges, Pick Rooms)
4. \quality\ (Ingestion Quarantine, CAT-6 AI Proposal Staging, Field Provenance, Reconciliation Candidates)
5. \ingestion\ (Raw Payload Captures, Ingestion Runs, Provider Checkpoints, Data Source Registry)
6. \udit\ (Immutable Tamper-Evident HMAC SHA-256 Audit Logs)

## 2. Real PostgreSQL Backup and Restore Workflow
The disaster recovery workflow is verified by \	ests/test_phase30_backup_disaster_recovery.py\:
1. **Source Provisioning**: Generates a isolated test database from the \cinevault\ template.
2. **Representative State Seeding**: Inserts active records across all 6 schemas, including multi-table joins and 384-dimensional pgvector embeddings.
3. **Binary Custom Dump**: Executes \pg_dump -U <user> -d <src_db> -F c -f /tmp/<src_db>.dump\ inside the PostgreSQL container.
4. **Source Destruction**: Completely drops the source database (\DROP DATABASE <src_db>\) to simulate disaster/data loss.
5. **Clean Target Provisioning**: Creates an empty recovery database (\CREATE DATABASE <rec_db>\).
6. **Binary Custom Restore**: Executes \pg_restore -U <user> -d <rec_db> /tmp/<src_db>.dump\.
7. **Integrity Verification**:
   - Verifies all 6 schemas exist and contain restored tables.
   - Verifies canonical records, credits, genres.
   - Verifies personal library, watch events, ratings, notes, reviews, collections, and streaks.
   - Verifies social friendships, recommendations, clubs, challenges, pick rooms, and pgvector cosine distance operations (\	aste_vector <=> target_vector\).
   - Verifies CAT-6 AI proposal staging and ingestion runs.
   - Verifies foreign key constraints are strictly active and enforceable in the restored database.
8. **Teardown**: Drops disposable databases and cleans temporary container dump files.

## 3. RPO and RTO Targets
- **Recovery Point Objective (RPO)**: < 5 minutes (WAL archiving & automated dump schedules).
- **Recovery Time Objective (RTO)**: < 1 hour (Fast pg_restore custom format decompression).
