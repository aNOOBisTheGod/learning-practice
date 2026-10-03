BEGIN;

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    number text NOT NULL UNIQUE CHECK (btrim(number) <> ''),
    server_serial text NOT NULL UNIQUE CHECK (btrim(server_serial) <> ''),
    specification jsonb NOT NULL CHECK (jsonb_typeof(specification) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE components (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    kind text NOT NULL CHECK (btrim(kind) <> ''),
    model text NOT NULL CHECK (btrim(model) <> ''),
    serial text NOT NULL CHECK (btrim(serial) <> ''),
    UNIQUE (order_id, serial)
);

CREATE TABLE test_runs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    plan_version text NOT NULL CHECK (btrim(plan_version) <> ''),
    engineer text NOT NULL CHECK (btrim(engineer) <> ''),
    configuration_matches boolean NOT NULL,
    open_defects integer NOT NULL CHECK (open_defects >= 0),
    results jsonb NOT NULL CHECK (jsonb_typeof(results) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
