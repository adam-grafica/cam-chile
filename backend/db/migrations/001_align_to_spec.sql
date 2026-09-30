-- Migración 001: alinear el esquema existente al estándar de AGENT_OPERATING_PROMPT.md
-- Idempotente: safe de correr múltiples veces.
-- Detecta DB legacy con esquema antiguo y migra a cameras(spec).

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS cameras_new (
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

-- Solo copiar si existe la tabla legacy 'cameras' (esquema antiguo)
INSERT OR IGNORE INTO cameras_new (id, name, country, region, city, latitude, longitude,
                                   source_name, source_url, stream_type, stream_url,
                                   public_status, license_or_terms_url, last_checked_at)
SELECT
    id,
    name,
    'CL'                                       AS country,
    NULL                                       AS region,
    address                                    AS city,
    lat                                        AS latitude,
    lon                                        AS longitude,
    'legacy_seed'                              AS source_name,
    'https://github.com/adam-grafica/cam-chile' AS source_url,
    CASE WHEN feed_type='youtube' THEN 'youtube_embed' ELSE 'iframe' END AS stream_type,
    stream_url,
    'unknown'                                  AS public_status,  -- requiere catalog pass manual
    NULL                                       AS license_or_terms_url,
    COALESCE(last_updated, strftime('%Y-%m-%dT%H:%M:%SZ','now')) AS last_checked_at
FROM cameras
WHERE name IS NOT NULL AND lat IS NOT NULL AND lon IS NOT NULL
  AND EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='cameras');

DROP TABLE IF EXISTS cameras;
ALTER TABLE cameras_new RENAME TO cameras;

CREATE INDEX IF NOT EXISTS idx_cameras_country  ON cameras(country);
CREATE INDEX IF NOT EXISTS idx_cameras_region   ON cameras(region);
CREATE INDEX IF NOT EXISTS idx_cameras_status   ON cameras(public_status);
CREATE INDEX IF NOT EXISTS idx_cameras_stream   ON cameras(stream_type);

COMMIT;