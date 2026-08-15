# CineVault OS — Batch Ingestion Runner & Large-Scale Scale Orchestrator
# Executes controlled, batched ingestion runs with metrics tracking, timing measurements, and partial failure recovery (Day 7 Expansion)

import time
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from .pipeline import pipeline_engine
from ..schemas.internal import IngestionTriggerRequest, IngestionItemPayload

logger = logging.getLogger("cinevault.ingestion.batch_runner")

class BatchRunner:
    """Orchestrates multi-batch ingestion runs for large-scale catalog expansion."""

    async def execute_staged_expansion(
        self,
        db: Optional[AsyncSession],
        provider_name: str,
        items: List[IngestionItemPayload],
        dry_run: bool = True,
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Executes catalog ingestion in controlled chunks (e.g. 500 records per batch).
        Tracks timing breakdown (total time, DB time, records/sec), quality statistics, and batch progress.
        """
        start_time = time.time()
        provider = provider_name.upper()
        total_items = len(items)

        if batch_size <= 0:
            batch_size = 500

        # Chunk items into batches
        batches = [items[i:i + batch_size] for i in range(0, total_items, batch_size)]

        total_seen = 0
        total_valid = 0
        total_rejected = 0
        total_created = 0
        total_updated = 0
        total_conflicted = 0
        total_needs_review = 0
        total_duplicates = 0
        total_errors = 0

        batch_details = []
        completed_batches = 0
        failed_batches = 0

        logger.info(f"Starting batch runner for {provider}: {total_items} candidates in {len(batches)} batches (dry_run={dry_run})")

        for b_idx, batch_items in enumerate(batches, start=1):
            batch_id = f"batch-{b_idx:03d}"
            b_start = time.time()

            trigger_req = IngestionTriggerRequest(
                provider_name=provider,
                dry_run=dry_run,
                items=batch_items
            )

            try:
                run_res = await pipeline_engine.execute_run(db=db, trigger_req=trigger_req)
                if db is not None:
                    await db.flush()

                b_duration = time.time() - b_start
                b_status = run_res.get("status", "COMPLETED")

                seen = run_res.get("records_seen", len(batch_items))
                valid = run_res.get("records_valid", 0)
                rejected = run_res.get("records_rejected", 0)
                created = run_res.get("records_created", 0)
                updated = run_res.get("records_updated", 0)
                conflicted = run_res.get("records_conflicted", 0)
                needs_rev = run_res.get("needs_review_count", 0)
                dups = run_res.get("duplicate_count", 0)
                errs = run_res.get("error_count", 0)

                total_seen += seen
                total_valid += valid
                total_rejected += rejected
                total_created += created
                total_updated += updated
                total_conflicted += conflicted
                total_needs_review += needs_rev
                total_duplicates += dups
                total_errors += errs

                if b_status in ("COMPLETED", "PARTIAL"):
                    completed_batches += 1
                else:
                    failed_batches += 1

                batch_details.append({
                    "batch_id": batch_id,
                    "ingestion_run_id": run_res.get("run_id"),
                    "status": b_status,
                    "records_seen": seen,
                    "records_valid": valid,
                    "records_created": created,
                    "records_updated": updated,
                    "duplicate_count": dups,
                    "conflicts": conflicted,
                    "duration_sec": round(b_duration, 4),
                    "records_per_sec": round(seen / b_duration, 2) if b_duration > 0 else 0.0
                })

            except Exception as batch_err:
                b_duration = time.time() - b_start
                failed_batches += 1
                if db is not None:
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                logger.error(f"Batch {batch_id} failed with exception: {batch_err}", exc_info=True)
                batch_details.append({
                    "batch_id": batch_id,
                    "ingestion_run_id": None,
                    "status": "FAILED",
                    "error": str(batch_err),
                    "records_seen": len(batch_items),
                    "duration_sec": round(b_duration, 4)
                })

        total_duration = time.time() - start_time
        records_per_sec = round(total_seen / total_duration, 2) if total_duration > 0 else 0.0

        return {
            "provider_name": provider,
            "dry_run": dry_run,
            "total_candidates": total_items,
            "total_batches": len(batches),
            "completed_batches": completed_batches,
            "failed_batches": failed_batches,
            "total_duration_sec": round(total_duration, 4),
            "records_per_sec": records_per_sec,
            "records_seen": total_seen,
            "records_valid": total_valid,
            "records_rejected": total_rejected,
            "records_created": total_created,
            "records_updated": total_updated,
            "records_conflicted": total_conflicted,
            "needs_review": total_needs_review,
            "duplicates": total_duplicates,
            "new_candidates": total_valid - total_duplicates,
            "existing_matches": total_duplicates,
            "error_count": total_errors,
            "batch_details": batch_details
        }

batch_runner = BatchRunner()
