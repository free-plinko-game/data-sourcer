-- Migration: Add combined_data to casinos table
-- Run this in Supabase SQL Editor if you already have the casinos table

-- Add combined_data column to store merged scraped data per casino
ALTER TABLE casinos ADD COLUMN IF NOT EXISTS combined_data JSONB;

-- Add combined_data_updated_at column to track when data was last merged
ALTER TABLE casinos ADD COLUMN IF NOT EXISTS combined_data_updated_at TIMESTAMPTZ;

-- Create index for faster queries on casinos with data
CREATE INDEX IF NOT EXISTS idx_casinos_combined_data ON casinos ((combined_data IS NOT NULL));
