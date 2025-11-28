-- Supabase Schema for Data Sourcer
-- Run this in Supabase SQL Editor to set up your database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Casinos table
CREATE TABLE IF NOT EXISTS casinos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    login_url TEXT,
    username TEXT,
    password TEXT,  -- Store encrypted or use Supabase Vault for production
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    combined_data JSONB,  -- Combined scraped data from all sources
    combined_data_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scrape configurations table
CREATE TABLE IF NOT EXISTS scrape_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casino_id UUID NOT NULL REFERENCES casinos(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    page_url TEXT NOT NULL,
    requires_login BOOLEAN DEFAULT false,
    extraction_type TEXT DEFAULT 'casino_info',
    custom_prompt TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scrape jobs table (for batch scraping with combined results)
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casino_id UUID REFERENCES casinos(id) ON DELETE CASCADE,
    name TEXT,
    status TEXT DEFAULT 'pending',
    total_urls INTEGER DEFAULT 0,
    completed_urls INTEGER DEFAULT 0,
    failed_urls INTEGER DEFAULT 0,
    combined_data JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Scraped data table
CREATE TABLE IF NOT EXISTS scraped_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    casino_id UUID NOT NULL REFERENCES casinos(id) ON DELETE CASCADE,
    config_id UUID REFERENCES scrape_configs(id) ON DELETE SET NULL,
    job_id UUID REFERENCES scrape_jobs(id) ON DELETE SET NULL,
    source_url TEXT NOT NULL,
    raw_html TEXT,
    extracted_data JSONB,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_scrape_configs_casino_id ON scrape_configs(casino_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_casino_id ON scrape_jobs(casino_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraped_data_casino_id ON scraped_data(casino_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_config_id ON scraped_data(config_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_job_id ON scraped_data(job_id);
CREATE INDEX IF NOT EXISTS idx_scraped_data_status ON scraped_data(status);
CREATE INDEX IF NOT EXISTS idx_scraped_data_scraped_at ON scraped_data(scraped_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_casinos_updated_at ON casinos;
CREATE TRIGGER update_casinos_updated_at
    BEFORE UPDATE ON casinos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_scrape_configs_updated_at ON scrape_configs;
CREATE TRIGGER update_scrape_configs_updated_at
    BEFORE UPDATE ON scrape_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (optional - enable if you want to restrict access)
-- ALTER TABLE casinos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scrape_configs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scraped_data ENABLE ROW LEVEL SECURITY;
