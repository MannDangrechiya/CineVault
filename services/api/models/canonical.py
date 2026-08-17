# CineVault OS — Canonical Schema ORM Models
# Maps PostgreSQL canonical schema tables (CAT-1) enforcing ADR-001, ADR-002, and Physical Database Design V1

from datetime import datetime, date
from typing import List, Optional
import uuid
from sqlalchemy import (
    Column, String, Text, SmallInteger, Integer, Boolean, Date, DateTime, ForeignKey, PrimaryKeyConstraint, Table, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# =========================================================================
# Taxonomy & Lookup Models
# =========================================================================

class ContentTypeModel(Base):
    __tablename__ = "content_type"
    __table_args__ = {"schema": "canonical"}

    content_type_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type_name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class GenreModel(Base):
    __tablename__ = "genre"
    __table_args__ = {"schema": "canonical"}

    genre_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class ThemeModel(Base):
    __tablename__ = "theme"
    __table_args__ = {"schema": "canonical"}

    theme_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class KeywordModel(Base):
    __tablename__ = "keyword"
    __table_args__ = {"schema": "canonical"}

    keyword_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

class CreditRoleModel(Base):
    __tablename__ = "credit_role"
    __table_args__ = {"schema": "canonical"}

    credit_role_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)

class CertificationModel(Base):
    __tablename__ = "certification"
    __table_args__ = {"schema": "canonical"}

    certification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    certification_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rating_body: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    meaning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_age: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

class ProductionCompanyModel(Base):
    __tablename__ = "production_company"
    __table_args__ = {"schema": "canonical"}

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

# =========================================================================
# Bridge / Join Tables
# =========================================================================

class TitleGenreModel(Base):
    __tablename__ = "title_genre"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "genre_id"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    genre_id: Mapped[str] = mapped_column(String(64), ForeignKey("canonical.genre.genre_id", ondelete="CASCADE"))

class TitleThemeModel(Base):
    __tablename__ = "title_theme"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "theme_id"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    theme_id: Mapped[str] = mapped_column(String(64), ForeignKey("canonical.theme.theme_id", ondelete="CASCADE"))

class TitleKeywordModel(Base):
    __tablename__ = "title_keyword"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "keyword_id"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    keyword_id: Mapped[str] = mapped_column(String(64), ForeignKey("canonical.keyword.keyword_id", ondelete="CASCADE"))

class TitleCountryModel(Base):
    __tablename__ = "title_country"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "country_code"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    country_code: Mapped[str] = mapped_column(String(2))

class TitleLanguageModel(Base):
    __tablename__ = "title_lang"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "language_code"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    language_code: Mapped[str] = mapped_column(String(3), nullable=False)

class TitleCertificationModel(Base):
    __tablename__ = "title_certification"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "certification_id"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    certification_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.certification.certification_id", ondelete="CASCADE"))
    note: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    certification: Mapped[CertificationModel] = relationship("CertificationModel")

class TitleCompanyModel(Base):
    __tablename__ = "title_company"
    __table_args__ = {"schema": "canonical"}

    title_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.production_company.company_id", ondelete="RESTRICT"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="PRODUCTION", nullable=False) # 'STUDIO', 'NETWORK', 'DISTRIBUTOR', 'PRODUCTION'

    company: Mapped[ProductionCompanyModel] = relationship("ProductionCompanyModel")
    title: Mapped["TitleModel"] = relationship("TitleModel", back_populates="companies")

# =========================================================================
# Core Title Hierarchy (Title → Edition → Release) & (Title → Season → Episode)
# =========================================================================

class TitleAliasModel(Base):
    __tablename__ = "title_alias"
    __table_args__ = {"schema": "canonical"}

    alias_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"), nullable=False)
    alias_name: Mapped[str] = mapped_column(String(512), nullable=False)
    alias_type: Mapped[str] = mapped_column(String(64), default="ALTERNATIVE", nullable=False)
    language_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    title: Mapped["TitleModel"] = relationship("TitleModel", back_populates="aliases")

class TitleModel(Base):
    __tablename__ = "title"
    __table_args__ = {"schema": "canonical"}

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    content_type_id: Mapped[str] = mapped_column(String(32), ForeignKey("canonical.content_type.content_type_id"), nullable=False)
    canonical_title: Mapped[str] = mapped_column(String(512), nullable=False)
    original_title: Mapped[str] = mapped_column(String(512), nullable=False)
    production_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    poster_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    backdrop_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    poster_sync_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    metadata_synced_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    aliases: Mapped[List[TitleAliasModel]] = relationship("TitleAliasModel", back_populates="title", cascade="all, delete-orphan")
    editions: Mapped[List["EditionModel"]] = relationship("EditionModel", back_populates="title", cascade="all, delete-orphan")
    seasons: Mapped[List["SeasonModel"]] = relationship("SeasonModel", back_populates="title", cascade="all, delete-orphan")
    credits: Mapped[List["CreditModel"]] = relationship("CreditModel", back_populates="title", cascade="all, delete-orphan")
    companies: Mapped[List[TitleCompanyModel]] = relationship("TitleCompanyModel", back_populates="title", cascade="all, delete-orphan")
    certifications: Mapped[List[TitleCertificationModel]] = relationship("TitleCertificationModel", cascade="all, delete-orphan")
    external_ids: Mapped[List["TitleExternalIdModel"]] = relationship("TitleExternalIdModel", back_populates="title", cascade="all, delete-orphan")
    genres: Mapped[List[GenreModel]] = relationship("GenreModel", secondary="canonical.title_genre")
    themes: Mapped[List[ThemeModel]] = relationship("ThemeModel", secondary="canonical.title_theme")
    keywords: Mapped[List[KeywordModel]] = relationship("KeywordModel", secondary="canonical.title_keyword")
    countries: Mapped[List[TitleCountryModel]] = relationship("TitleCountryModel", cascade="all, delete-orphan")
    languages: Mapped[List[TitleLanguageModel]] = relationship("TitleLanguageModel", cascade="all, delete-orphan")
    awards: Mapped[List["AwardResultModel"]] = relationship("AwardResultModel", back_populates="title", cascade="all, delete-orphan")
    festival_participations: Mapped[List["FestivalParticipationModel"]] = relationship("FestivalParticipationModel", back_populates="title", cascade="all, delete-orphan")
    franchise_entries: Mapped[List["FranchiseEntryModel"]] = relationship("FranchiseEntryModel", cascade="all, delete-orphan")
    platform_offers: Mapped[List["PlatformOfferModel"]] = relationship("PlatformOfferModel", back_populates="title", cascade="all, delete-orphan")

class EditionModel(Base):
    __tablename__ = "edition"
    __table_args__ = {"schema": "canonical"}

    edition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    edition_name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    runtime_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aspect_ratio: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    color_format: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sound_mix: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    title: Mapped[TitleModel] = relationship("TitleModel", back_populates="editions")
    releases: Mapped[List["ReleaseModel"]] = relationship("ReleaseModel", back_populates="edition", cascade="all, delete-orphan")

class ReleaseModel(Base):
    __tablename__ = "release"
    __table_args__ = {"schema": "canonical"}

    release_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.edition.edition_id", ondelete="CASCADE"), nullable=False)
    release_name: Mapped[str] = mapped_column(String(256), nullable=False)
    release_type: Mapped[str] = mapped_column(String(64), nullable=False)
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    edition: Mapped[EditionModel] = relationship("EditionModel", back_populates="releases")

class SeasonModel(Base):
    __tablename__ = "season"
    __table_args__ = {"schema": "canonical"}

    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    season_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    title: Mapped[TitleModel] = relationship("TitleModel", back_populates="seasons")
    episodes: Mapped[List["EpisodeModel"]] = relationship("EpisodeModel", back_populates="season", cascade="all, delete-orphan")

class EpisodeModel(Base):
    __tablename__ = "episode"
    __table_args__ = {"schema": "canonical"}

    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.season.season_id", ondelete="RESTRICT"), nullable=False)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    air_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    runtime_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    season: Mapped[SeasonModel] = relationship("SeasonModel", back_populates="episodes")
    regional_orders: Mapped[List["RegionalEpisodeOrderModel"]] = relationship("RegionalEpisodeOrderModel", back_populates="episode", cascade="all, delete-orphan")

class RegionalEpisodeOrderModel(Base):
    __tablename__ = "regional_episode_order"
    __table_args__ = {"schema": "canonical"}

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.episode.episode_id", ondelete="CASCADE"), nullable=False)
    region_code: Mapped[str] = mapped_column(String(2), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    regional_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    episode: Mapped[EpisodeModel] = relationship("EpisodeModel", back_populates="regional_orders")

# =========================================================================
# People, Names, Credits & External Identifiers
# =========================================================================

class PersonModel(Base):
    __tablename__ = "person"
    __table_args__ = {"schema": "canonical"}

    person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(256), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    death_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    names: Mapped[List["PersonNameModel"]] = relationship("PersonNameModel", back_populates="person", cascade="all, delete-orphan")
    credits: Mapped[List["CreditModel"]] = relationship("CreditModel", back_populates="person", cascade="all, delete-orphan")
    external_ids: Mapped[List["PersonExternalIdModel"]] = relationship("PersonExternalIdModel", cascade="all, delete-orphan")

class PersonNameModel(Base):
    __tablename__ = "person_name"
    __table_args__ = {"schema": "canonical"}

    name_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.person.person_id", ondelete="CASCADE"), nullable=False)
    name_type: Mapped[str] = mapped_column(String(64), default="PRIMARY", nullable=False) # 'PRIMARY', 'ALIAS', 'TRANSLITERATED'
    name_value: Mapped[str] = mapped_column(String(256), nullable=False)
    language_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    person: Mapped[PersonModel] = relationship("PersonModel", back_populates="names")

class CreditModel(Base):
    __tablename__ = "credit"
    __table_args__ = {"schema": "canonical"}

    credit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    edition_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.edition.edition_id", ondelete="SET NULL"), nullable=True)
    person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.person.person_id", ondelete="RESTRICT"), nullable=False)
    credit_role_id: Mapped[str] = mapped_column(String(64), ForeignKey("canonical.credit_role.credit_role_id"), nullable=False)
    character_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    billing_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    title: Mapped[TitleModel] = relationship("TitleModel", back_populates="credits")
    person: Mapped[PersonModel] = relationship("PersonModel", back_populates="credits")
    role: Mapped[CreditRoleModel] = relationship("CreditRoleModel")

class TitleExternalIdModel(Base):
    __tablename__ = "title_external_id"
    __table_args__ = {"schema": "canonical"}

    mapping_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    title: Mapped[TitleModel] = relationship("TitleModel", back_populates="external_ids")

class PersonExternalIdModel(Base):
    __tablename__ = "person_external_id"
    __table_args__ = {"schema": "canonical"}

    mapping_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.person.person_id", ondelete="CASCADE"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

# =========================================================================
# Universes, Franchises & Viewing Orders
# =========================================================================

class UniverseModel(Base):
    __tablename__ = "universe"
    __table_args__ = {"schema": "canonical"}

    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class FranchiseModel(Base):
    __tablename__ = "franchise"
    __table_args__ = {"schema": "canonical"}

    franchise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    universe_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.universe.universe_id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)

    entries: Mapped[List["FranchiseEntryModel"]] = relationship("FranchiseEntryModel", back_populates="franchise", cascade="all, delete-orphan")
    viewing_orders: Mapped[List["ViewingOrderModel"]] = relationship("ViewingOrderModel", back_populates="franchise", cascade="all, delete-orphan")

class FranchiseEntryModel(Base):
    __tablename__ = "franchise_entry"
    __table_args__ = {"schema": "canonical"}

    franchise_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.franchise.franchise_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(64), default="CANONICAL", nullable=False)

    franchise: Mapped[FranchiseModel] = relationship("FranchiseModel", back_populates="entries")

class ViewingOrderModel(Base):
    __tablename__ = "viewing_order"
    __table_args__ = {"schema": "canonical"}

    viewing_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.franchise.franchise_id", ondelete="CASCADE"), nullable=False)
    order_name: Mapped[str] = mapped_column(String(256), nullable=False)
    order_type: Mapped[str] = mapped_column(String(64), default="CHRONOLOGICAL", nullable=False)

    franchise: Mapped[FranchiseModel] = relationship("FranchiseModel", back_populates="viewing_orders")
    items: Mapped[List["ViewingOrderItemModel"]] = relationship("ViewingOrderItemModel", back_populates="viewing_order", cascade="all, delete-orphan")

class ViewingOrderItemModel(Base):
    __tablename__ = "viewing_order_item"
    __table_args__ = {"schema": "canonical"}

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    viewing_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.viewing_order.viewing_order_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    viewing_order: Mapped[ViewingOrderModel] = relationship("ViewingOrderModel", back_populates="items")

# =========================================================================
# Awards & Festivals
# =========================================================================

class AwardModel(Base):
    __tablename__ = "award"
    __table_args__ = {"schema": "canonical"}

    award_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    award_name: Mapped[str] = mapped_column(String(256), nullable=False)
    organization: Mapped[str] = mapped_column(String(256), nullable=False)

    categories: Mapped[List["AwardCategoryModel"]] = relationship("AwardCategoryModel", back_populates="award", cascade="all, delete-orphan")
    events: Mapped[List["AwardEventModel"]] = relationship("AwardEventModel", back_populates="award", cascade="all, delete-orphan")

class AwardCategoryModel(Base):
    __tablename__ = "award_category"
    __table_args__ = {"schema": "canonical"}

    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    award_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.award.award_id", ondelete="CASCADE"), nullable=False)
    category_name: Mapped[str] = mapped_column(String(256), nullable=False)

    award: Mapped[AwardModel] = relationship("AwardModel", back_populates="categories")

class AwardEventModel(Base):
    __tablename__ = "award_event"
    __table_args__ = {"schema": "canonical"}

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    award_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.award.award_id", ondelete="CASCADE"), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    edition_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    award: Mapped[AwardModel] = relationship("AwardModel", back_populates="events")
    results: Mapped[List["AwardResultModel"]] = relationship("AwardResultModel", back_populates="event", cascade="all, delete-orphan")

class AwardResultModel(Base):
    __tablename__ = "award_result"
    __table_args__ = {"schema": "canonical"}

    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.award_event.event_id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.award_category.category_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=True)
    person_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.person.person_id", ondelete="RESTRICT"), nullable=True)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    event: Mapped[AwardEventModel] = relationship("AwardEventModel", back_populates="results")
    category: Mapped[AwardCategoryModel] = relationship("AwardCategoryModel")
    title: Mapped[Optional[TitleModel]] = relationship("TitleModel", back_populates="awards")
    person: Mapped[Optional[PersonModel]] = relationship("PersonModel")

class FestivalModel(Base):
    __tablename__ = "festival"
    __table_args__ = {"schema": "canonical"}

    festival_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    festival_name: Mapped[str] = mapped_column(String(256), nullable=False)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    editions: Mapped[List["FestivalEditionModel"]] = relationship("FestivalEditionModel", back_populates="festival", cascade="all, delete-orphan")

class FestivalEditionModel(Base):
    __tablename__ = "festival_edition"
    __table_args__ = {"schema": "canonical"}

    festival_edition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    festival_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.festival.festival_id", ondelete="CASCADE"), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    edition_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    festival: Mapped[FestivalModel] = relationship("FestivalModel", back_populates="editions")
    participations: Mapped[List["FestivalParticipationModel"]] = relationship("FestivalParticipationModel", back_populates="festival_edition", cascade="all, delete-orphan")

class FestivalParticipationModel(Base):
    __tablename__ = "festival_participation"
    __table_args__ = {"schema": "canonical"}

    participation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    festival_edition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.festival_edition.festival_edition_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    section_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    festival_edition: Mapped[FestivalEditionModel] = relationship("FestivalEditionModel", back_populates="participations")
    title: Mapped[TitleModel] = relationship("TitleModel", back_populates="festival_participations")

# =========================================================================
# Identity Redirect & Platform Offer Models
# =========================================================================

class IdentityRedirectModel(Base):
    __tablename__ = "identity_redirect"
    __table_args__ = {"schema": "canonical"}

    redirect_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    merge_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    merged_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class PlatformModel(Base):
    __tablename__ = "platform"
    __table_args__ = {"schema": "canonical"}

    platform_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    offers: Mapped[List["PlatformOfferModel"]] = relationship("PlatformOfferModel", back_populates="platform", cascade="all, delete-orphan")

class PlatformOfferModel(Base):
    __tablename__ = "platform_offer"
    __table_args__ = {"schema": "canonical"}

    offer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.platform.platform_id", ondelete="RESTRICT"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    title: Mapped[TitleModel] = relationship("TitleModel", back_populates="platform_offers")
    platform: Mapped[PlatformModel] = relationship("PlatformModel", back_populates="offers")

class StreamingProviderModel(Base):
    __tablename__ = "streaming_provider"
    __table_args__ = {"schema": "canonical"}

    provider_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    home_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    offers: Mapped[List["StreamingOfferModel"]] = relationship("StreamingOfferModel", back_populates="provider", cascade="all, delete-orphan")

class StreamingOfferModel(Base):
    __tablename__ = "streaming_offer"
    __table_args__ = {"schema": "canonical"}

    offer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), ForeignKey("canonical.streaming_provider.provider_id"), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(32), nullable=False) # 'subscription', 'rent', 'buy', 'free', 'ad_supported'
    price_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    web_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(3, 2), default=1.00, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    provider: Mapped[StreamingProviderModel] = relationship("StreamingProviderModel", back_populates="offers")

