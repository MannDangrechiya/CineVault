# CineVault OS — Day 3 Data Model & ERD Foundation Test Suite
# Verifies schema integrity, ORM mappings, baseline catalog counts, personal data isolation, and auth compatibility.

import pytest
import asyncio
from services.api.models.canonical import (
    TitleModel, EditionModel, ReleaseModel, SeasonModel, EpisodeModel,
    UniverseModel, FranchiseModel, FranchiseEntryModel, ViewingOrderModel, ViewingOrderItemModel,
    PersonModel, CreditModel, CreditRoleModel, TitleExternalIdModel, PersonExternalIdModel,
    TitleLanguageModel, GenreModel, ContentTypeModel
)
from services.api.models.personal import (
    LibraryEntryModel, WatchEventModel, UserTitleStateModel, RatingModel, NoteModel, ReviewModel
)
from services.api.repositories.canonical import canonical_repository, SEED_FALLBACK_TITLES
from services.api.routers.auth import _load_local_user_store, _generate_local_dev_jwt


class TestDay3DataModelERDFoundation:
    """Automated test suite validating Day 3 Data Model specifications, ORM entities, and baselines."""

    def test_baseline_catalog_counts(self):
        """Verify baseline catalog returns exactly 9 Movies and 1 TV Series (10 Total)."""
        titles = asyncio.run(canonical_repository.list_titles(db=None))
        assert len(titles) == 10, f"Expected exactly 10 catalog titles, got {len(titles)}"

        movies = [t for t in titles if t.content_type == "MOVIE"]
        tv_series = [t for t in titles if t.content_type == "TV_SERIES"]

        assert len(movies) == 9, f"Expected 9 movies, got {len(movies)}"
        assert len(tv_series) == 1, f"Expected 1 TV series, got {len(tv_series)}"

    def test_canonical_orm_model_mappings(self):
        """Verify all canonical domain models are mapped to the correct tables and schemas."""
        assert TitleModel.__tablename__ == "title"
        assert TitleModel.__table_args__["schema"] == "canonical"

        assert EditionModel.__tablename__ == "edition"
        assert ReleaseModel.__tablename__ == "release"

        assert SeasonModel.__tablename__ == "season"
        assert SeasonModel.__table_args__["schema"] == "canonical"

        assert EpisodeModel.__tablename__ == "episode"
        assert EpisodeModel.__table_args__["schema"] == "canonical"

        assert UniverseModel.__tablename__ == "universe"
        assert FranchiseModel.__tablename__ == "franchise"
        assert FranchiseEntryModel.__tablename__ == "franchise_entry"
        assert ViewingOrderModel.__tablename__ == "viewing_order"
        assert ViewingOrderItemModel.__tablename__ == "viewing_order_item"

        assert TitleExternalIdModel.__tablename__ == "title_external_id"
        assert PersonExternalIdModel.__tablename__ == "person_external_id"
        assert TitleLanguageModel.__tablename__ == "title_lang"

    def test_personal_data_isolation(self):
        """Verify canonical TitleModel contains NO personal data fields (watched, rating, favorite, notes)."""
        canonical_columns = [col.name for col in TitleModel.__table__.columns]
        
        forbidden_personal_fields = [
            "watched", "favorite", "personal_rating", "rating",
            "notes", "user_progress", "user_status", "user_id"
        ]
        
        for field in forbidden_personal_fields:
            assert field not in canonical_columns, f"Personal field '{field}' erroneously present in canonical.title!"

        # Verify personal tables belong strictly to 'personal' schema
        assert LibraryEntryModel.__table_args__[1]["schema"] == "personal"
        assert WatchEventModel.__table_args__["schema"] == "personal"
        assert UserTitleStateModel.__table_args__[1]["schema"] == "personal"
        assert RatingModel.__table_args__["schema"] == "personal"
        assert NoteModel.__table_args__["schema"] == "personal"
        assert ReviewModel.__table_args__["schema"] == "personal"

    def test_external_id_mapping_structure(self):
        """Verify external provider mapping schema supports provider_name and external_id without hardcoding."""
        ext_cols = [col.name for col in TitleExternalIdModel.__table__.columns]
        assert "mapping_id" in ext_cols
        assert "title_id" in ext_cols
        assert "provider_name" in ext_cols
        assert "external_id" in ext_cols
        assert "external_url" in ext_cols

        person_ext_cols = [col.name for col in PersonExternalIdModel.__table__.columns]
        assert "mapping_id" in person_ext_cols
        assert "person_id" in person_ext_cols
        assert "provider_name" in person_ext_cols
        assert "external_id" in person_ext_cols

    def test_authentication_identity_compatibility(self):
        """Verify authenticated identity store & JWT generation remain 100% functional."""
        store = _load_local_user_store()
        assert "dev@cinevault.local" in store
        dev_user = store["dev@cinevault.local"]
        assert dev_user["user_id"] == "018f0000-0000-7000-8000-000000000001"

        token = _generate_local_dev_jwt(
            user_id=dev_user["user_id"],
            email="dev@cinevault.local",
            username="dev",
            roles=dev_user["roles"]
        )
        assert isinstance(token, str)
        assert len(token) > 20
