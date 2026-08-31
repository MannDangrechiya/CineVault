# CineVault OS — Media & Artwork URL Resolution Unit & Integration Tests

import unittest
from services.api.media_resolver import (
    resolve_poster_url,
    resolve_backdrop_url,
    normalize_media_url,
    TMDB_POSTER_BASE_URL,
    TMDB_BACKDROP_BASE_URL,
)
from services.api.ingestion.adapters import (
    TmdbProviderAdapter,
    TvdbProviderAdapter,
    AniListProviderAdapter,
    MyAnimeListProviderAdapter,
)


class TestMediaUrlResolution(unittest.TestCase):
    """Tests canonical media URL resolver functionality across scenarios."""

    def test_absolute_https_urls(self):
        url = "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg"
        self.assertEqual(resolve_poster_url(url), url)
        self.assertEqual(resolve_backdrop_url(url), url)

        amazon_url = "https://m.media-amazon.com/images/M/MV5BOTdmNTgyNDUt.jpg"
        self.assertEqual(resolve_poster_url(amazon_url), amazon_url)

    def test_insecure_http_upgrade(self):
        insecure_url = "http://image.tmdb.org/t/p/w500/sample.jpg"
        expected = "https://image.tmdb.org/t/p/w500/sample.jpg"
        self.assertEqual(resolve_poster_url(insecure_url), expected)

    def test_provider_relative_paths(self):
        rel_path = "/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg"
        expected_poster = f"{TMDB_POSTER_BASE_URL}{rel_path}"
        expected_backdrop = f"{TMDB_BACKDROP_BASE_URL}{rel_path}"

        self.assertEqual(resolve_poster_url(rel_path), expected_poster)
        self.assertEqual(resolve_backdrop_url(rel_path), expected_backdrop)

    def test_relative_path_without_leading_slash(self):
        rel_path = "oYuLEW92A1s3pX76M9T20Xx.jpg"
        expected_poster = f"{TMDB_POSTER_BASE_URL}/{rel_path}"
        self.assertEqual(resolve_poster_url(rel_path), expected_poster)

    def test_local_asset_paths(self):
        local_poster = "/assets/posters/custom.jpg"
        local_image = "/images/backdrops/custom.png"
        self.assertEqual(resolve_poster_url(local_poster), local_poster)
        self.assertEqual(resolve_backdrop_url(local_image), local_image)

    def test_empty_and_null_fallbacks(self):
        self.assertIsNone(resolve_poster_url(None))
        self.assertIsNone(resolve_poster_url(""))
        self.assertIsNone(resolve_poster_url("   "))
        self.assertIsNone(resolve_poster_url("null"))
        self.assertIsNone(resolve_poster_url("None"))
        self.assertIsNone(resolve_poster_url("undefined"))

    def test_wrong_poster_isolation(self):
        """Ensures distinct titles resolve strictly to their own artwork."""
        parasite_poster = "/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg"
        inception_poster = "/oYuLEW92A1s3pX76M9T20Xx.jpg"

        resolved_parasite = resolve_poster_url(parasite_poster)
        resolved_inception = resolve_poster_url(inception_poster)

        self.assertNotEqual(resolved_parasite, resolved_inception)
        self.assertIn("7IiTTgloJzvGI1TAYGlC2z2zOZB", resolved_parasite)
        self.assertIn("oYuLEW92A1s3pX76M9T20Xx", resolved_inception)


class TestIngestionProviderArtworkExtraction(unittest.TestCase):
    """Tests provider adapters extract and normalize artwork metadata properly."""

    def setUp(self):
        self.tmdb_adapter = TmdbProviderAdapter()
        self.tvdb_adapter = TvdbProviderAdapter()
        self.anilist_adapter = AniListProviderAdapter()
        self.mal_adapter = MyAnimeListProviderAdapter()

    def test_tmdb_adapter_extracts_artwork(self):
        raw = {
            "id": 496243,
            "title": "Parasite",
            "release_date": "2019-05-30",
            "poster_path": "/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg",
            "backdrop_path": "/hiKmpZMGZOSXAAtWwhZIz6wXxpy.jpg",
            "overview": "Class drama",
        }
        normalized = self.tmdb_adapter.normalize_payload(raw)
        self.assertEqual(
            normalized["poster_url"],
            "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg"
        )
        self.assertEqual(
            normalized["backdrop_url"],
            "https://image.tmdb.org/t/p/w1280/hiKmpZMGZOSXAAtWwhZIz6wXxpy.jpg"
        )

    def test_tvdb_adapter_extracts_artwork(self):
        raw = {
            "id": 393187,
            "name": "Severance",
            "year": "2022",
            "image": "https://image.tmdb.org/t/p/w500/1XddXPXbAh2g2Ur5KNvV26C5W.jpg",
            "overview": "Office thriller",
        }
        normalized = self.tvdb_adapter.normalize_payload(raw)
        self.assertEqual(
            normalized["poster_url"],
            "https://image.tmdb.org/t/p/w500/1XddXPXbAh2g2Ur5KNvV26C5W.jpg"
        )

    def test_anilist_adapter_extracts_artwork(self):
        raw = {
            "id": 21,
            "title": {"english": "One Piece", "native": "ONE PIECE"},
            "coverImage": {"large": "https://cdn.myanimelist.net/images/anime/1/21.jpg"},
            "bannerImage": "https://cdn.myanimelist.net/images/anime/1/21_banner.jpg",
        }
        normalized = self.anilist_adapter.normalize_payload(raw)
        self.assertEqual(
            normalized["poster_url"],
            "https://cdn.myanimelist.net/images/anime/1/21.jpg"
        )
        self.assertEqual(
            normalized["backdrop_url"],
            "https://cdn.myanimelist.net/images/anime/1/21_banner.jpg"
        )


if __name__ == "__main__":
    unittest.main()
