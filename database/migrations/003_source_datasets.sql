-- ============================================================
-- Migration 003: Staging tables for user-supplied source datasets
-- address-table1.csv and address-table2.csv
-- ============================================================
-- These mirror the source CSV structure 1:1 (Requirement: "Load both CSV files
-- into the PostgreSQL database, creating raw address tables that mirror the
-- source structure"). They are landing/staging tables -- the production
-- pipeline still flows through `raw_addresses` (see 001_initial_schema.sql),
-- which scripts/ingest_datasets.py populates from these staging tables.

-- ─── staging_table1_county_street ────────────────────────────────────────────
-- Source: address-table1.csv (county_name, street_nbr, street_name, zip5)
-- Known data quality issues: ~29% exact duplicates, missing street_nbr (~8%),
-- house-number ranges/junk ("75-81", "OFF", "09-Nov"), ~24% missing zip5,
-- no city/state at all.

CREATE TABLE IF NOT EXISTS staging_table1_county_street (
  id              BIGSERIAL PRIMARY KEY,
  county_name     TEXT,
  street_nbr      TEXT,            -- kept as raw TEXT: source has non-numeric values
  street_name     TEXT,
  zip5            TEXT,            -- kept as TEXT to preserve leading zeros / blanks
  source_file     VARCHAR(100) DEFAULT 'address-table1.csv',
  row_number      INTEGER,         -- 1-based line number in the source CSV, for traceability
  ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stg_t1_county   ON staging_table1_county_street (county_name);
CREATE INDEX IF NOT EXISTS idx_stg_t1_zip      ON staging_table1_county_street (zip5);

-- ─── staging_table2_city_address ─────────────────────────────────────────────
-- Source: address-table2.csv (city, countyOrParish, stateOrProvince, address, shortAddress)
-- Known data quality issues: a handful of sentinel "Out-of State"/zip 99999 rows,
-- lot-prefixed rural addresses ("L6.21 Stony Creek Rd"), inline unit/apt/lot
-- identifiers embedded in the address string, small number of exact duplicates.

CREATE TABLE IF NOT EXISTS staging_table2_city_address (
  id                BIGSERIAL PRIMARY KEY,
  city              TEXT,
  county_or_parish  TEXT,
  state_or_province TEXT,
  address           TEXT,          -- full, already-formatted address (treated as ground truth)
  short_address     TEXT,          -- street-only portion of `address`
  source_file       VARCHAR(100) DEFAULT 'address-table2.csv',
  row_number        INTEGER,
  ingested_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stg_t2_county   ON staging_table2_city_address (county_or_parish);
CREATE INDEX IF NOT EXISTS idx_stg_t2_city     ON staging_table2_city_address (city);
CREATE INDEX IF NOT EXISTS idx_stg_t2_state    ON staging_table2_city_address (state_or_province);

-- ─── ingestion_log ────────────────────────────────────────────────────────────
-- One row per ingestion run, for auditability of bulk loads (separate from the
-- per-event `audit_trail` table, which logs individual address standardizations).

CREATE TABLE IF NOT EXISTS ingestion_log (
  id                 BIGSERIAL PRIMARY KEY,
  source_file        VARCHAR(100) NOT NULL,
  rows_in_file        INTEGER NOT NULL,
  rows_inserted_staging INTEGER NOT NULL,
  rows_inserted_raw_addresses INTEGER NOT NULL,
  rows_skipped        INTEGER NOT NULL,
  skip_reasons        JSONB,
  started_at          TIMESTAMPTZ NOT NULL,
  finished_at         TIMESTAMPTZ NOT NULL
);
