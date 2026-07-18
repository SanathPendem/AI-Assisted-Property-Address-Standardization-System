-- ============================================================
-- Migration 002: pgvector extension for address embeddings
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to canonical_addresses
ALTER TABLE canonical_addresses
  ADD COLUMN IF NOT EXISTS embedding vector(384);  -- all-MiniLM-L6-v2 dimensions

-- IVFFlat index for approximate nearest-neighbor search
-- listcount = sqrt(num_rows), tune as data grows
CREATE INDEX IF NOT EXISTS idx_canonical_embedding
  ON canonical_addresses
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- View: returns top-N similar canonical addresses for a query vector
-- Usage: SELECT * FROM find_similar_canonicals('[0.1,0.2,...]'::vector, 5);
CREATE OR REPLACE FUNCTION find_similar_canonicals(
  query_embedding vector(384),
  top_k           INT DEFAULT 5
)
RETURNS TABLE (
  id              UUID,
  full_address    TEXT,
  normalized_key  TEXT,
  similarity      FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ca.id,
    ca.full_address,
    ca.normalized_key,
    1 - (ca.embedding <=> query_embedding) AS similarity
  FROM canonical_addresses ca
  WHERE ca.embedding IS NOT NULL
  ORDER BY ca.embedding <=> query_embedding
  LIMIT top_k;
END;
$$ LANGUAGE plpgsql;
