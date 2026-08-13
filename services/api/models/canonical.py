# CineVault OS — Canonical Schema ORM Models
# Maps PostgreSQL canonical schema tables (CAT-1) enforcing ADR-001, ADR-002, and Physical Database Design V1

from datetime import datetime, date
from typing import List, Optional
import uuid
from sqlalchemy import (
    Column, String, Text, SmallInteger, Integer, Boolean, Date, DateTime, ForeignKey, PrimaryKeyConstraint, Table
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

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

class CreditRoleModel(Base):
    __tablename__ = "credit_role"
    __table_args__ = {"schema": "canonical"}

    credit_role_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)

class TitleGenreModel(Base):
    __tablename__ = "title_genre"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "genre_id"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    genre_id: Mapped[str] = mapped_column(String(64), ForeignKey("canonical.genre.genre_id", ondelete="CASCADE"))

class TitleCountryModel(Base):
    __tablename__ = "title_country"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "country_code"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    country_code: Mapped[str] = mapped_column(String(2))

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
    status_flag: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    editions: Mapped[List["EditionModel"]] = relationship("EditionModel", back_populates="title", cascade="all, delete-orphan")
    external_ids: Mapped[List["TitleExternalIdModel"]] = relationship("TitleExternalIdModel", back_populates="title", cascade="all, delete-orphan")
    genres: Mapped[List[GenreModel]] = relationship("GenreModel", secondary="canonical.title_genre")
    countries: Mapped[List[TitleCountryModel]] = relationship("TitleCountryModel", cascade="all, delete-orphan")
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

class PersonModel(Base):
    __tablename__ = "person"
    __table_args__ = {"schema": "canonical"}

    person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(256), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    death_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

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

class SeasonModel(Base):
    __tablename__ = "season"
    __table_args__ = {"schema": "canonical"}

    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    season_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

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

class FranchiseEntryModel(Base):
    __tablename__ = "franchise_entry"
    __table_args__ = {"schema": "canonical"}

    franchise_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.franchise.franchise_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(64), default="CANONICAL", nullable=False)

class ViewingOrderModel(Base):
    __tablename__ = "viewing_order"
    __table_args__ = {"schema": "canonical"}

    viewing_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.franchise.franchise_id", ondelete="CASCADE"), nullable=False)
    order_name: Mapped[str] = mapped_column(String(256), nullable=False)
    order_type: Mapped[str] = mapped_column(String(64), default="CHRONOLOGICAL", nullable=False)

class ViewingOrderItemModel(Base):
    __tablename__ = "viewing_order_item"
    __table_args__ = {"schema": "canonical"}

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    viewing_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.viewing_order.viewing_order_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

class TitleLanguageModel(Base):
    __tablename__ = "title_lang"
    __table_args__ = (
        PrimaryKeyConstraint("title_id", "language_code"),
        {"schema": "canonical"}
    )

    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"))
    language_code: Mapped[str] = mapped_column(String(3), nullable=False)

