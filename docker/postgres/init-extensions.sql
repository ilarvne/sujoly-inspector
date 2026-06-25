-- PostgreSQL extensions for Zhambyl Hydraulic Structures Catalog
-- postgis: spatial types and indexing (system of record for vector features)
-- vector: pgvector for similarity search (pgvector Python adapter)
-- pg_trgm: trigram fuzzy matching (installed now for Phase 2, avoids future migration)

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
