
CREATE TABLE IF NOT EXISTS apartments (
    id SERIAL PRIMARY KEY,
    listing_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    poi JSONB
);
