-- Tworzenie użytkownika root z pełnymi uprawnieniami
CREATE ROLE root WITH LOGIN PASSWORD 'root123' SUPERUSER CREATEDB CREATEROLE;

-- Tworzenie bazy danych app_user
CREATE DATABASE app_db OWNER root;
GRANT ALL PRIVILEGES ON DATABASE app_db TO root;

-- Połączenie z bazą app_user i tworzenie rozszerzeń
\c app_user

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;


INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext)
VALUES (
    4326, 
    'EPSG', 
    4326, 
    '+proj=longlat +datum=WGS84 +no_defs',
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
) ON CONFLICT (srid) DO NOTHING;
