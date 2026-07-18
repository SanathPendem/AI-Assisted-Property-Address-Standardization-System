-- ============================================================
-- Migration 001: Initial Schema
-- Address Standardization System
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── ENUM Types ──────────────────────────────────────────────────────────────

CREATE TYPE routing_decision AS ENUM (
  'auto_accepted',
  'pending_review',
  'flagged'
);

CREATE TYPE review_status AS ENUM (
  'pending',
  'accepted',
  'corrected',
  'rejected',
  'escalated'
);

CREATE TYPE human_decision AS ENUM (
  'accepted',
  'corrected',
  'rejected'
);

-- ─── canonical_addresses ─────────────────────────────────────────────────────
-- Deduplicated, standardized address master records

CREATE TABLE canonical_addresses (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  house_number     VARCHAR(20),
  pre_directional  VARCHAR(10),
  street_name      VARCHAR(200) NOT NULL,
  street_suffix    VARCHAR(50),
  post_directional VARCHAR(10),
  unit_type        VARCHAR(30),
  unit_number      VARCHAR(30),
  city             VARCHAR(100),
  state            VARCHAR(50),
  state_abbr       CHAR(2),
  zip_code         VARCHAR(10),
  zip_plus4        VARCHAR(5),
  country          VARCHAR(50) DEFAULT 'USA',
  full_address     TEXT NOT NULL,          -- Human-readable canonical form
  normalized_key   TEXT NOT NULL UNIQUE,  -- Normalized key for dedup lookup
  source_count     INTEGER DEFAULT 1,      -- How many raw addresses resolved here
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_normalized_key ON canonical_addresses (normalized_key);
CREATE INDEX idx_canonical_zip_code       ON canonical_addresses (zip_code);
CREATE INDEX idx_canonical_state_abbr     ON canonical_addresses (state_abbr);

-- ─── raw_addresses ───────────────────────────────────────────────────────────
-- Every ingested raw address string

CREATE TABLE raw_addresses (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  raw_text           TEXT NOT NULL,
  source_system      VARCHAR(100),          -- Which DB/system this came from
  source_record_id   VARCHAR(200),          -- External record ID for traceability
  parsed_components  JSONB,                 -- libpostal parse output
  canonical_id       UUID REFERENCES canonical_addresses(id) ON DELETE SET NULL,
  created_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_canonical_id  ON raw_addresses (canonical_id);
CREATE INDEX idx_raw_source        ON raw_addresses (source_system, source_record_id);
CREATE INDEX idx_raw_parsed        ON raw_addresses USING GIN (parsed_components);

-- ─── standardization_results ─────────────────────────────────────────────────
-- ML pipeline output for each standardization request

CREATE TABLE standardization_results (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  raw_address_id      UUID NOT NULL REFERENCES raw_addresses(id) ON DELETE CASCADE,
  canonical_id        UUID REFERENCES canonical_addresses(id) ON DELETE SET NULL,
  predicted_address   TEXT NOT NULL,
  confidence_score    NUMERIC(5,4) NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
  routing_decision    routing_decision NOT NULL,
  feature_vector      JSONB,               -- Feature values used by the model
  model_version       VARCHAR(50),         -- Which model version was used
  processing_time_ms  INTEGER,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_results_raw_address   ON standardization_results (raw_address_id);
CREATE INDEX idx_results_canonical     ON standardization_results (canonical_id);
CREATE INDEX idx_results_confidence    ON standardization_results (confidence_score);
CREATE INDEX idx_results_routing       ON standardization_results (routing_decision);

-- ─── review_queue ────────────────────────────────────────────────────────────
-- Items routed for human review

CREATE TABLE review_queue (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  standardization_id     UUID NOT NULL REFERENCES standardization_results(id) ON DELETE CASCADE,
  raw_address_id         UUID NOT NULL REFERENCES raw_addresses(id) ON DELETE CASCADE,
  raw_address_text       TEXT NOT NULL,
  predicted_address      TEXT NOT NULL,
  confidence_score       NUMERIC(5,4) NOT NULL,
  routing_decision       routing_decision NOT NULL,
  priority_score         NUMERIC(5,4) DEFAULT 0.5, -- Active learning priority (0=low, 1=high)
  review_status          review_status DEFAULT 'pending',
  reviewer_id            VARCHAR(100),
  reviewed_at            TIMESTAMPTZ,
  similar_canonicals     JSONB,             -- Top-N similar canonical addresses for reviewer
  context_notes          TEXT,              -- System-generated context for reviewer
  created_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_queue_status    ON review_queue (review_status);
CREATE INDEX idx_queue_priority  ON review_queue (priority_score DESC) WHERE review_status = 'pending';
CREATE INDEX idx_queue_created   ON review_queue (created_at DESC);

-- ─── feedback ────────────────────────────────────────────────────────────────
-- Human corrections stored as training data

CREATE TABLE feedback (
  id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  review_queue_id       UUID REFERENCES review_queue(id) ON DELETE SET NULL,
  raw_address_id        UUID NOT NULL REFERENCES raw_addresses(id) ON DELETE CASCADE,
  raw_address_text      TEXT NOT NULL,
  original_prediction   TEXT NOT NULL,
  human_decision        human_decision NOT NULL,
  corrected_address     TEXT,              -- Null if decision = 'accepted'
  reviewer_id           VARCHAR(100) NOT NULL,
  rationale             TEXT,
  used_in_training      BOOLEAN DEFAULT FALSE,
  training_batch_id     VARCHAR(50),       -- Which retraining batch used this
  created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_decision     ON feedback (human_decision);
CREATE INDEX idx_feedback_training     ON feedback (used_in_training) WHERE used_in_training = FALSE;
CREATE INDEX idx_feedback_created      ON feedback (created_at DESC);

-- ─── audit_trail ─────────────────────────────────────────────────────────────
-- Immutable log of every system event

CREATE TABLE audit_trail (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type          VARCHAR(50) NOT NULL,  -- standardized, review_submitted, retrained, etc.
  raw_address_id      UUID REFERENCES raw_addresses(id) ON DELETE SET NULL,
  raw_address_text    TEXT,
  predicted_address   TEXT,
  final_address       TEXT,
  confidence_score    NUMERIC(5,4),
  routing_decision    routing_decision,
  human_decision      human_decision,
  human_rationale     TEXT,
  reviewer_id         VARCHAR(100),
  model_version       VARCHAR(50),
  metadata            JSONB,               -- Any extra event-specific data
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_event_type   ON audit_trail (event_type);
CREATE INDEX idx_audit_created      ON audit_trail (created_at DESC);
CREATE INDEX idx_audit_raw_address  ON audit_trail (raw_address_id);

-- ─── model_registry ──────────────────────────────────────────────────────────
-- Track model versions and retraining history

CREATE TABLE model_registry (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  version          VARCHAR(50) NOT NULL UNIQUE,
  artifact_path    TEXT NOT NULL,
  training_samples INTEGER,
  accuracy         NUMERIC(5,4),
  precision_score  NUMERIC(5,4),
  recall_score     NUMERIC(5,4),
  f1_score         NUMERIC(5,4),
  training_log     JSONB,
  is_active        BOOLEAN DEFAULT FALSE,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_model_active ON model_registry (is_active) WHERE is_active = TRUE;

-- ─── Triggers: updated_at ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_canonical_addresses_updated_at
  BEFORE UPDATE ON canonical_addresses
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── Seed: Initial model registry placeholder ─────────────────────────────────

INSERT INTO model_registry (version, artifact_path, training_samples, accuracy, is_active)
VALUES ('v0.0.0-baseline', '/app/models/lgbm_model.pkl', 0, NULL, TRUE);
