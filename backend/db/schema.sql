-- CAM-CHILE — Schema canónico (alineado a AGENT_OPERATING_PROMPT.md §Estándar)
-- Una sola tabla: cameras
-- Migración inicial: backend/db/migrations/001_align_to_spec.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cameras (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    name                  TEXT    NOT NULL,
    country               TEXT    NOT NULL DEFAULT 'CL',
    region                TEXT,
    city                  TEXT,
    latitude              REAL    NOT NULL CHECK (latitude  BETWEEN -90  AND 90),
    longitude             REAL    NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    source_name           TEXT    NOT NULL,
    source_url            TEXT    NOT NULL,
    stream_type           TEXT    NOT NULL CHECK (stream_type IN ('youtube','youtube_embed','hls','mp4','iframe')),
    stream_url            TEXT    NOT NULL,
    public_status         TEXT    NOT NULL CHECK (public_status IN ('declared_public','unknown','revoked')),
    license_or_terms_url  TEXT,
    last_checked_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    created_at            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (source_name, stream_url)
);

CREATE INDEX IF NOT EXISTS idx_cameras_country  ON cameras(country);
CREATE INDEX IF NOT EXISTS idx_cameras_region   ON cameras(region);
CREATE INDEX IF NOT EXISTS idx_cameras_status   ON cameras(public_status);
CREATE INDEX IF NOT EXISTS idx_cameras_stream   ON cameras(stream_type);