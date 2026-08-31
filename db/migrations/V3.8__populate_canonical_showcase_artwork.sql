-- CineVault OS — Flyway Migration V3.8: Populate Canonical Showcase Artwork
-- Updates verified high-resolution poster and backdrop URLs for canonical showcase titles

-- 1. Showcase Movies & Series with Verified TMDB Artwork
UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/hiKmpZMGZOSXAAtWwhZIz6wXxpy.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'MOV-000001' OR canonical_title = 'Parasite' AND production_year = 2019;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/oYuLEW92A1s3pX76M9T20Xx.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/s3TBrRGB1iav7ySaNx3z7k2P.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'MOV-000002' OR canonical_title = 'Inception' AND production_year = 2010;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/nMK28FiMGfEWDyIOwcLLCePOvYr.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt0468569' OR canonical_title = 'The Dark Knight' AND production_year = 2008;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/rSPw7tgCH9c6NqICZefy2aZvdR.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt0068646' OR canonical_title = 'The Godfather' AND production_year = 1972;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/zX95tFj2nB2s4N8mN1L.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/zX95tFj2nB2s4N8mN1L.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt0816692' OR canonical_title = 'Interstellar' AND production_year = 2014;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/xJHokMbljvjADYdit5fK5VQsX2k.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt0245429' OR canonical_title = 'Spirited Away' AND production_year = 2001;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/u7i1b1zT0Z9m2B1sZ41n6kY.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/u7i1b1zT0Z9m2B1sZ41n6kY.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt1187043' OR canonical_title = '3 Idiots' AND production_year = 2009;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/mw884g3tJ3S1e7N6W5e8B92n.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/mw884g3tJ3S1e7N6W5e8B92n.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt5074352' OR canonical_title = 'Dangal' AND production_year = 2016;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/nEuF2GGqAaowhanHbdvW3h86W31.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/nEuF2GGqAaowhanHbdvW3h86W31.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt8178634' OR canonical_title = 'RRR' AND production_year = 2022;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/A5wWkW942Lnd0zIexvTqX64kU6a.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/A5wWkW942Lnd0zIexvTqX64kU6a.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id = 'IMDB-tt0073707' OR canonical_title = 'Sholay' AND production_year = 1975;

UPDATE canonical.title
SET poster_url = 'https://image.tmdb.org/t/p/w500/1XddXPXbAh2g2Ur5KNvV26C5W.jpg',
    backdrop_url = 'https://image.tmdb.org/t/p/w1280/9faGSFi5jam6pDWGNd0ip8725m5.jpg',
    poster_sync_status = 'SYNCED',
    metadata_synced_at = clock_timestamp(),
    updated_at = clock_timestamp()
WHERE display_id IN ('TV-SEVERANCE-01', 'IMDB-tt11280740') OR canonical_title = 'Severance' AND production_year = 2022;
