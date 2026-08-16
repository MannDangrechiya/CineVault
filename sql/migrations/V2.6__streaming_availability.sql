-- CineVault OS — Migration V2.6: Streaming Availability & Temporal Regional Offers
-- Models licensed streaming availability, offer types (subscription, rent, buy, free, ad_supported), validity windows, and source verification

CREATE TABLE IF NOT EXISTS canonical.streaming_provider (
    provider_id VARCHAR(64) PRIMARY KEY,
    provider_name VARCHAR(128) NOT NULL,
    logo_url VARCHAR(512),
    home_url VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS canonical.streaming_offer (
    offer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title_id UUID NOT NULL REFERENCES canonical.title(title_id) ON DELETE CASCADE,
    provider_id VARCHAR(64) NOT NULL REFERENCES canonical.streaming_provider(provider_id),
    country_code VARCHAR(2) NOT NULL,
    offer_type VARCHAR(32) NOT NULL, -- 'subscription', 'rent', 'buy', 'free', 'ad_supported'
    price_amount NUMERIC(10, 2),
    currency_code VARCHAR(3),
    web_url VARCHAR(512),
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
    valid_until TIMESTAMP WITH TIME ZONE,
    last_verified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
    source_name VARCHAR(64) NOT NULL,
    confidence_score NUMERIC(3, 2) NOT NULL DEFAULT 1.00,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_streaming_offer_title_country ON canonical.streaming_offer(title_id, country_code, is_active);
CREATE INDEX IF NOT EXISTS idx_streaming_offer_validity ON canonical.streaming_offer(valid_from, valid_until, last_verified_at);
