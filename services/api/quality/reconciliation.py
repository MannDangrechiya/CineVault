# CineVault OS — Domain Reconciliation & Merge Protection Engine
# Resolves cross-source metadata conflicts using domain authority rules and governs canonical merges (DS-01, ADR-003, ADR-004)

import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .identity_resolution import MatchState

logger = logging.getLogger("cinevault.quality.reconciliation")

class ReconciliationEngine:
    """Applies domain authority matrix, governs metadata conflict lifecycle, and enforces merge protection gates."""

    AUTHORITY_MATRIX = {
        "OFFICIAL_STUDIO": {
            "primary_domains": ["OFFICIAL_TITLE", "RELEASE_DATE", "CREDITS"],
            "rule_id": "RULE-OFFICIAL-STUDIO-PRIMARY",
            "weight": 1.00
        },
        "OFFICIAL_FESTIVAL": {
            "primary_domains": ["AWARDS", "FESTIVAL_PROGRAM"],
            "rule_id": "RULE-OFFICIAL-FESTIVAL-PRIMARY",
            "weight": 1.00
        },
        "KOBIS": {
            "primary_domains": ["KOREAN_FILM", "KOREAN_BOX_OFFICE", "KOREAN_CAST"],
            "rule_id": "RULE-KOREAN-FILM-PRIMARY-KOBIS",
            "weight": 1.00
        },
        "TVDB": {
            "primary_domains": ["TV_SERIES_STRUCTURE", "EPISODE_ORDER", "SEASON_HIERARCHY"],
            "rule_id": "RULE-TVDB-SECONDARY-TV",
            "weight": 0.95
        },
        "TMDB": {
            "primary_domains": ["GLOBAL_SYNOPSIS", "GLOBAL_ARTWORK"],
            "rule_id": "RULE-TMDB-GLOBAL-CANDIDATE",
            "weight": 0.85
        },
        "ANILIST": {
            "primary_domains": ["ANIME_METADATA", "EPISODE_COUNT"],
            "rule_id": "RULE-ANILIST-ANIME-PRIMARY",
            "weight": 0.90
        },
        "MYANIMELIST": {
            "primary_domains": ["ANIME_SYNOPSIS"],
            "rule_id": "RULE-MAL-ANIME-SECONDARY",
            "weight": 0.85
        },
        "WIKIDATA": {
            "primary_domains": ["CROSS_REF_IDS"],
            "rule_id": "RULE-WIKIDATA-IDENTITY-MAP",
            "weight": 0.60
        }
    }

    def resolve_attribute_conflict(
        self,
        attribute_name: str,
        observations: List[Dict[str, Any]],
        domain_type: str = "GLOBAL"
    ) -> Dict[str, Any]:
        """
        Resolves conflicting attribute observations based on domain authority weighting.
        Does NOT use blind last-write-wins.
        """
        best_obs = None
        best_weight = -1.0

        for obs in observations:
            provider = (obs.get("provider_name") or "UNKNOWN").upper()
            val = obs.get("value")
            if val is None:
                continue

            auth = self.AUTHORITY_MATRIX.get(provider, {"weight": 0.50, "rule_id": "RULE-DEFAULT-FALLBACK"})
            weight = auth["weight"]

            # Elevate domain specific primary authority
            if domain_type == "KOREAN_FILM" and provider == "KOBIS":
                weight = 1.00
            elif domain_type == "TV_SERIES" and provider == "TVDB":
                weight = 0.95
            elif domain_type == "ANIME" and provider in ("ANILIST", "MYANIMELIST"):
                weight = 0.90

            if weight > best_weight:
                best_weight = weight
                best_obs = {
                    "attribute_name": attribute_name,
                    "winning_value": val,
                    "winning_provider": provider,
                    "applied_rule_id": auth.get("rule_id", "RULE-DEFAULT-FALLBACK"),
                    "confidence_score": weight
                }

        return best_obs or {
            "attribute_name": attribute_name,
            "winning_value": None,
            "winning_provider": "NONE",
            "applied_rule_id": "RULE-NO-OBSERVATION",
            "confidence_score": 0.00
        }

    def verify_merge_safety(
        self,
        source_entity: Dict[str, Any],
        target_entity: Dict[str, Any],
        user_personal_data_attached: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Canonical Merge Protection Gate (ADR-003, ADR-004):
        Verifies that merging two canonical entities will not corrupt user personal data or violate identity boundaries.
        Returns (is_safe, list_of_blocking_reasons).
        """
        blocking_reasons: List[str] = []

        # 1. Content Type Mismatch Gate
        if source_entity.get("content_type") != target_entity.get("content_type"):
            blocking_reasons.append(
                f"MERGE_BLOCKED: Content type mismatch ({source_entity.get('content_type')} vs {target_entity.get('content_type')}). Controlled reclassification required."
            )

        # 2. Production Year Discrepancy Gate (> 1 year difference)
        s_year = source_entity.get("production_year")
        t_year = target_entity.get("production_year")
        if s_year and t_year and abs(s_year - t_year) > 1:
            blocking_reasons.append(
                f"MERGE_BLOCKED: Production year discrepancy ({s_year} vs {t_year}). Possible remake/adaptation boundary violation."
            )

        # 3. User Personal Data Protection Gate (ADR-003)
        if user_personal_data_attached:
            blocking_reasons.append(
                "MERGE_BLOCKED: User personal data (watch events/ratings/reviews) attached to source entity. Automated merge prohibited; user review required."
            )

        is_safe = len(blocking_reasons) == 0
        if not is_safe:
            logger.warning(f"Canonical Merge Gate Blocked: {blocking_reasons}")
        return is_safe, blocking_reasons

    async def execute_title_merge(
        self,
        db: Any,
        source_title_id: uuid.UUID,
        target_title_id: uuid.UUID,
        merge_reason: str = "MANUAL_OR_AUTO_DEDUPLICATION",
        user_personal_data_attached: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a canonical merge adhering to ADR-003 and DEC-PHYS-PRP-06:
        1. Validates merge safety rules.
        2. Soft-deletes source title (status_flag='RETIRED').
        3. Creates canonical.identity_redirect record (from_id -> to_id).
        4. Re-points external IDs from source to target.
        """
        from ..models.canonical import TitleModel, TitleExternalIdModel, IdentityRedirectModel
        from sqlalchemy import select

        # Fetch source and target
        stmt_s = select(TitleModel).where(TitleModel.title_id == source_title_id)
        stmt_t = select(TitleModel).where(TitleModel.title_id == target_title_id)
        res_s = await db.execute(stmt_s)
        res_t = await db.execute(stmt_t)
        source = res_s.scalars().first()
        target = res_t.scalars().first()

        if not source or not target:
            raise ValueError("Source or target title not found for merge execution")

        # Verify safety
        source_dict = {
            "content_type": source.content_type_id,
            "production_year": source.production_year,
            "canonical_title": source.canonical_title
        }
        target_dict = {
            "content_type": target.content_type_id,
            "production_year": target.production_year,
            "canonical_title": target.canonical_title
        }

        is_safe, blocking = self.verify_merge_safety(source_dict, target_dict, user_personal_data_attached=user_personal_data_attached)
        if not is_safe:
            raise RuntimeError(f"Merge execution aborted by safety gate: {blocking}")

        # 1. Create IdentityRedirectModel
        redirect_orm = IdentityRedirectModel(
            redirect_id=uuid.uuid4(),
            from_id=source_title_id,
            to_id=target_title_id,
            entity_type="TITLE",
            merge_reason=merge_reason,
            merged_at=datetime.now(timezone.utc)
        )
        db.add(redirect_orm)

        # 2. Re-point external IDs that don't conflict
        ext_stmt = select(TitleExternalIdModel).where(TitleExternalIdModel.title_id == source_title_id)
        ext_res = await db.execute(ext_stmt)
        source_exts = ext_res.scalars().all()
        for ext in source_exts:
            t_ext_stmt = select(TitleExternalIdModel).where(
                TitleExternalIdModel.title_id == target_title_id,
                TitleExternalIdModel.provider_name == ext.provider_name
            )
            t_ext_res = await db.execute(t_ext_stmt)
            if not t_ext_res.scalars().first():
                ext.title_id = target_title_id

        # 3. Mark source title as RETIRED (Tombstone pattern)
        source.status_flag = "RETIRED"
        source.updated_at = datetime.now(timezone.utc)

        await db.flush()
        return {
            "status": "MERGED",
            "redirect_id": str(redirect_orm.redirect_id),
            "from_id": str(source_title_id),
            "to_id": str(target_title_id),
            "merged_at": redirect_orm.merged_at.isoformat()
        }

reconciliation_engine = ReconciliationEngine()
