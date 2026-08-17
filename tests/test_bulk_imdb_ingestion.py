# CineVault OS — Tests for Bulk IMDb Ingestion Pipeline

import gzip
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from services.api.scripts.seed_bulk_imdb import (
    DEFAULT_MIN_VOTES,
    TITLE_TYPE_MAP,
    parse_qualified_ratings,
    process_and_import,
)


class TestBulkImdbIngestion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)

        # Create sample ratings TSV.GZ
        self.ratings_path = self.data_dir / "title.ratings.tsv.gz"
        ratings_data = (
            "tconst\taverageRating\tnumVotes\n"
            "tt0000001\t5.7\t2000\n"      # Qualified
            "tt0000002\t6.0\t100\n"       # Below min_votes (500)
            "tt0000003\t8.5\t500\n"       # Qualified (boundary)
            "tt0000004\t7.2\t150000\n"    # Qualified
        )
        with gzip.open(self.ratings_path, "wt", encoding="utf-8") as f:
            f.write(ratings_data)

        # Create sample basics TSV.GZ
        self.basics_path = self.data_dir / "title.basics.tsv.gz"
        basics_data = (
            "tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\tendYear\truntimeMinutes\tgenres\n"
            "tt0000001\tmovie\tCarmencita\tCarmencita\t0\t1894\t\\N\t1\tDocumentary,Short\n"
            "tt0000002\tmovie\tClown et ses chiens\tLe Clown et ses chiens\t0\t1892\t\\N\t5\tAnimation,Short\n"
            "tt0000003\ttvSeries\tBreaking Bad\tBreaking Bad\t0\t2008\t2013\t49\tCrime,Drama,Thriller\n"
            "tt0000004\ttvMiniSeries\tChernobyl\tChernobyl\t0\t2019\t2019\t330\tDrama,History,Thriller\n"
            "tt0000005\tshort\tShort Title\tShort Title\t0\t2020\t\\N\t10\tShort\n"  # Invalid titleType
        )
        with gzip.open(self.basics_path, "wt", encoding="utf-8") as f:
            f.write(basics_data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_qualified_ratings(self):
        qualified = parse_qualified_ratings(self.ratings_path, min_votes=500)
        self.assertIn("tt0000001", qualified)
        self.assertNotIn("tt0000002", qualified)
        self.assertIn("tt0000003", qualified)
        self.assertIn("tt0000004", qualified)
        self.assertEqual(len(qualified), 3)

    def test_title_type_mapping(self):
        self.assertEqual(TITLE_TYPE_MAP["movie"], "movie")
        self.assertEqual(TITLE_TYPE_MAP["tvSeries"], "tv_series")
        self.assertEqual(TITLE_TYPE_MAP["tvMiniSeries"], "tv_series")

    def test_process_and_import_dry_run(self):
        import asyncio

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        stats = asyncio.run(
            process_and_import(
                db_pool=mock_pool,
                basics_path=self.basics_path,
                ratings_path=self.ratings_path,
                min_votes=500,
                dry_run=True,
            )
        )

        self.assertEqual(stats["qualified_ratings"], 3)
        self.assertEqual(stats["records_staged"], 3)  # tt0000001 (movie), tt0000003 (tvSeries), tt0000004 (tvMiniSeries)


if __name__ == "__main__":
    unittest.main()
