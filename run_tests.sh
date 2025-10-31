#!/usr/bin/env bash
set -euo pipefail

mkdir -p ./media/photos || true

# Load .env variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

export POSTGRES_HOST=localhost

# Ensure Postgres is up (published on localhost:5432 by docker-compose)
if ! nc -z localhost 5432 >/dev/null 2>&1; then
  echo "Starting postgres via docker compose..."
  docker compose up -d postgres >/dev/null
fi

echo -n "Waiting for postgres to be ready"
for i in {1..60}; do
  if nc -z localhost 5432 >/dev/null 2>&1; then
    echo " - ready"
    break
  fi
  echo -n "."
  sleep 1
done

# Clear database before running tests
echo "Clearing database..."
PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
DO \$\$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE;';
    END LOOP;
END
\$\$;
"

PYTHONPATH=. pytest -q
