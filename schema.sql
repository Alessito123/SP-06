CREATE TABLE IF NOT EXISTS p06_runs (
    run_id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    input_sha256 text NOT NULL CHECK (length(input_sha256) = 64),
    settings jsonb NOT NULL,
    metrics jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS p06_predictions (
    run_id uuid NOT NULL REFERENCES p06_runs ON DELETE CASCADE,
    series text NOT NULL,
    origin integer NOT NULL,
    horizon integer NOT NULL CHECK (horizon BETWEEN 1 AND 5),
    model text NOT NULL,
    observed double precision CHECK (observed >= 0),
    forecast double precision NOT NULL CHECK (forecast >= 0),
    lower90 double precision CHECK (lower90 BETWEEN 0 AND forecast),
    upper90 double precision CHECK (upper90 >= forecast),
    PRIMARY KEY (run_id, series, origin, horizon, model),
    CHECK ((lower90 IS NULL) = (upper90 IS NULL))
);
