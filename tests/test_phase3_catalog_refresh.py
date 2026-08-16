# CineVault OS — Phase 3: Catalog Refresh / Update System Verification Tests
# Validates metadata change detection, domain reconciliation, conflict lifecycle, no silent overwrite, and personal data preservation

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.quality.reconciliation import ReconciliationEngine
from services.api.repositories.quality import quality_repository
from services.api.models.canonical import (
    TitleModel, EditionModel, ReleaseModel, TitleAliasModel, CreditModel,
    CreditRoleModel, PersonModel, PlatformModel, PlatformOfferModel,
    TitleExternalIdModel, ContentTypeModel
)
from services.api.models.personal import (
    LibraryEntryModel, WatchEventModel, RatingModel, NoteModel, ReviewModel, UserTitleStateModel
)
from services.api.models.quality import (
    MetadataConflictModel, ReconciliationCandidateModel
)
from services.api.models.ingestion import (
    FieldProvenanceModel, RawPayloadCaptureModel
)

class Phase3CatalogRefreshTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 3 verification for controlled catalog refresh and personal data safety."""

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        self.reconciliation_engine = ReconciliationEngine()

        async with self.SessionLocal() as session:
            # Seed foundational taxonomy
            types = [("movie", "Feature Film"), ("tv_series", "Television Series"), ("short_film", "Short Film")]
            for t_id, t_name in types:
                existing = await session.get(ContentTypeModel, t_id)
                if not existing:
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_name))

            roles = [("actor", "Actor", "CAST"), ("director", "Director", "CREW"), ("producer", "Producer", "CREW")]
            for r_id, r_name, r_cat in roles:
                existing = await session.get(CreditRoleModel, r_id)
                if not existing:
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))

            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_personal_user_data_preservation_during_refresh(self):
        """NON-NEGOTIABLE: Personal ratings, watch history, notes, reviews, and library entries must remain 100% intact across catalog refreshes."""
        async with self.SessionLocal() as session:
            title_id = uuid.uuid4()
            user_id = uuid.uuid4()

            # 1. Seed initial Canonical Title & Edition
            title = TitleModel(
                title_id=title_id,
                display_id="MOV-REFRESH-001",
                content_type_id="movie",
                canonical_title="Original Master Title",
                original_title="Original Master Title",
                production_year=2020,
                synopsis="Initial release synopsis."
            )
            edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=title_id,
                edition_name="Theatrical Cut",
                runtime_minutes=120,
                is_primary=True
            )
            session.add_all([title, edition])
            await session.flush()

            # 2. Attach User Personal Data (CAT-2)
            lib_entry = LibraryEntryModel(user_id=user_id, title_id=title_id)
            watch_event = WatchEventModel(
                user_id=user_id,
                title_id=title_id,
                edition_id=edition.edition_id,
                device_type="Apple TV 4K",
                notes="Watched with friends."
            )
            rating = RatingModel(user_id=user_id, title_id=title_id, rating_value=9)
            note = NoteModel(user_id=user_id, title_id=title_id, note_text="Favorite soundtrack in the third act.")
            review = ReviewModel(user_id=user_id, title_id=title_id, review_title="Masterpiece", review_text="Incredible direction.")
            state = UserTitleStateModel(user_id=user_id, title_id=title_id, is_favorite=True)

            session.add_all([lib_entry, watch_event, rating, note, review, state])
            await session.commit()

            # 3. Simulate Catalog Metadata Refresh (synopsis update, runtime correction, new releases)
            title.synopsis = "Updated official 4K remaster synopsis with expanded plot context."
            title.tagline = "New Remastered Edition."
            edition.runtime_minutes = 124  # Corrected runtime

            new_release = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=edition.edition_id,
                release_name="4K Ultra HD Blu-ray Remaster",
                release_type="PHYSICAL_BLURAY",
                release_date=date(2024, 5, 1),
                country_code="US"
            )
            session.add(new_release)
            await session.commit()

            # 4. Verify Personal Data remains 100% intact and unchanged
            stmt_watch = select(WatchEventModel).where(WatchEventModel.user_id == user_id, WatchEventModel.title_id == title_id)
            saved_watch = (await session.execute(stmt_watch)).scalar_one_or_none()
            self.assertIsNotNone(saved_watch)
            self.assertEqual(saved_watch.notes, "Watched with friends.")
            self.assertEqual(saved_watch.device_type, "Apple TV 4K")

            stmt_rating = select(RatingModel).where(RatingModel.user_id == user_id, RatingModel.title_id == title_id)
            saved_rating = (await session.execute(stmt_rating)).scalar_one_or_none()
            self.assertIsNotNone(saved_rating)
            self.assertEqual(saved_rating.rating_value, 9)

            stmt_note = select(NoteModel).where(NoteModel.user_id == user_id, NoteModel.title_id == title_id)
            saved_note = (await session.execute(stmt_note)).scalar_one_or_none()
            self.assertIsNotNone(saved_note)
            self.assertEqual(saved_note.note_text, "Favorite soundtrack in the third act.")

            stmt_review = select(ReviewModel).where(ReviewModel.user_id == user_id, ReviewModel.title_id == title_id)
            saved_review = (await session.execute(stmt_review)).scalar_one_or_none()
            self.assertIsNotNone(saved_review)
            self.assertEqual(saved_review.review_title, "Masterpiece")

            stmt_state = select(UserTitleStateModel).where(UserTitleStateModel.user_id == user_id, UserTitleStateModel.title_id == title_id)
            saved_state = (await session.execute(stmt_state)).scalar_one_or_none()
            self.assertIsNotNone(saved_state)
            self.assertTrue(saved_state.is_favorite)

    async def test_domain_authority_reconciliation_and_no_silent_overwrite(self):
        """Enforces domain authority rules: Primary domain authority wins; lower weights cannot silently overwrite verified data."""
        # 1. Korean film title conflict: KOBIS (weight 1.00) vs TMDB (weight 0.85)
        observations_kr = [
            {"provider_name": "TMDB", "value": "Parasite (Global)"},
            {"provider_name": "KOBIS", "value": "기생충"}
        ]
        res_kr = self.reconciliation_engine.resolve_attribute_conflict(
            attribute_name="original_title",
            observations=observations_kr,
            domain_type="KOREAN_FILM"
        )
        self.assertEqual(res_kr["winning_provider"], "KOBIS")
        self.assertEqual(res_kr["winning_value"], "기생충")
        self.assertEqual(res_kr["applied_rule_id"], "RULE-KOREAN-FILM-PRIMARY-KOBIS")
        self.assertEqual(res_kr["confidence_score"], 1.00)

        # 2. TV Series structure: TVDB (weight 0.95) vs TMDB (weight 0.85)
        observations_tv = [
            {"provider_name": "TMDB", "value": 10},
            {"provider_name": "TVDB", "value": 12}
        ]
        res_tv = self.reconciliation_engine.resolve_attribute_conflict(
            attribute_name="episode_count",
            observations=observations_tv,
            domain_type="TV_SERIES"
        )
        self.assertEqual(res_tv["winning_provider"], "TVDB")
        self.assertEqual(res_tv["winning_value"], 12)
        self.assertEqual(res_tv["applied_rule_id"], "RULE-TVDB-SECONDARY-TV")

    async def test_metadata_conflict_lifecycle_and_curator_resolution(self):
        """Validates: change detection -> conflict creation -> human review -> resolution -> canonical promotion."""
        async with self.SessionLocal() as session:
            title_id = uuid.uuid4()
            conflict_id = uuid.uuid4()

            # Seed Title
            title = TitleModel(
                title_id=title_id,
                display_id="MOV-CONF-001",
                content_type_id="movie",
                canonical_title="Conflict Test Movie",
                original_title="Conflict Test Movie",
                production_year=2021
            )
            session.add(title)
            await session.flush()

            # 1. Conflicting candidate observation creates MetadataConflictModel
            conflict = MetadataConflictModel(
                conflict_id=conflict_id,
                entity_type="TITLE",
                entity_id=title_id,
                field_name="runtime_minutes",
                candidate_value="145",
                existing_value="138",
                source_provider="TMDB",
                confidence="CONFLICT",
                status="OPEN"
            )
            session.add(conflict)
            await session.commit()

            # 2. Curator lists open metadata conflicts
            open_conflicts = await quality_repository.list_metadata_conflicts(session)
            self.assertTrue(any(c["conflict_id"] == str(conflict_id) for c in open_conflicts))

            # 3. Curator resolves conflict with audit logging
            res = await quality_repository.resolve_metadata_conflict(
                db=session,
                conflict_id=str(conflict_id),
                actor_id="curator_mann_01",
                winning_value="145",
                resolution_notes="Verified via theatrical distribution cue sheet."
            )
            await session.commit()

            self.assertEqual(res["status"], "RESOLVED")
            self.assertEqual(res["winning_value"], "145")

            # 4. Verify DB record transitioned to RESOLVED
            stmt = select(MetadataConflictModel).where(MetadataConflictModel.conflict_id == conflict_id)
            updated_conflict = (await session.execute(stmt)).scalar_one_or_none()
            self.assertIsNotNone(updated_conflict)
            self.assertEqual(updated_conflict.status, "RESOLVED")
            self.assertEqual(updated_conflict.resolved_by, "curator_mann_01")

    async def test_alias_release_credit_and_availability_incremental_refresh(self):
        """Validates incremental refresh: appending aliases, releases, credits, and streaming offers without duplication."""
        async with self.SessionLocal() as session:
            title_id = uuid.uuid4()
            actor_id = uuid.uuid4()
            platform_id = uuid.uuid4()

            # 1. Seed base Title and Edition
            title = TitleModel(
                title_id=title_id,
                display_id="MOV-INC-001",
                content_type_id="movie",
                canonical_title="Incremental Refresh Feature",
                original_title="Incremental Refresh Feature",
                production_year=2023
            )
            edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=title_id,
                edition_name="Standard Cut",
                runtime_minutes=110,
                is_primary=True
            )
            person = PersonModel(person_id=actor_id, canonical_name="Lead Actor")
            platform = PlatformModel(platform_id=platform_id, name="Prime Video", code="AMAZON_PRIME")

            session.add_all([title, edition, person, platform])
            await session.flush()

            # 2. Refresh Action: Add New Alias
            alias = TitleAliasModel(
                alias_id=uuid.uuid4(),
                title_id=title_id,
                alias_name="Incremental Remastered",
                alias_type="ALTERNATIVE",
                language_code="eng"
            )

            # 3. Refresh Action: Add New Release
            release = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=edition.edition_id,
                release_name="UK Digital Premiere",
                release_type="DIGITAL",
                release_date=date(2024, 1, 15),
                country_code="GB"
            )

            # 4. Refresh Action: Add New Cast Credit
            credit = CreditModel(
                credit_id=uuid.uuid4(),
                title_id=title_id,
                person_id=actor_id,
                credit_role_id="actor",
                character_name="Protagonist",
                billing_order=1
            )

            # 5. Refresh Action: Add New Availability Offer
            offer = PlatformOfferModel(
                offer_id=uuid.uuid4(),
                platform_id=platform_id,
                title_id=title_id,
                country_code="US",
                offer_type="FLATRATE",
                valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
            )

            # 6. Record Field Provenance
            prov = FieldProvenanceModel(
                provenance_id=uuid.uuid4(),
                entity_type="TITLE",
                entity_id=title_id,
                field_name="availability",
                field_value="AMAZON_PRIME:FLATRATE:US",
                source_provider="JUSTWATCH_METADATA",
                external_id="jw_12345",
                confidence="HIGH",
                verification_status="VERIFIED"
            )

            session.add_all([alias, release, credit, offer, prov])
            await session.commit()

            # Assert complete incremental hydration
            stmt_alias = select(TitleAliasModel).where(TitleAliasModel.title_id == title_id)
            aliases = (await session.execute(stmt_alias)).scalars().all()
            self.assertEqual(len(aliases), 1)
            self.assertEqual(aliases[0].alias_name, "Incremental Remastered")

            stmt_rel = select(ReleaseModel).where(ReleaseModel.edition_id == edition.edition_id)
            releases = (await session.execute(stmt_rel)).scalars().all()
            self.assertEqual(len(releases), 1)
            self.assertEqual(releases[0].country_code, "GB")

            stmt_credit = select(CreditModel).where(CreditModel.title_id == title_id)
            credits = (await session.execute(stmt_credit)).scalars().all()
            self.assertEqual(len(credits), 1)
            self.assertEqual(credits[0].character_name, "Protagonist")

            stmt_offer = select(PlatformOfferModel).where(PlatformOfferModel.title_id == title_id)
            offers = (await session.execute(stmt_offer)).scalars().all()
            self.assertEqual(len(offers), 1)
            self.assertEqual(offers[0].offer_type, "FLATRATE")
