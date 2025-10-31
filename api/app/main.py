import os
import json
import redis
import psycopg2
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor, Json


# --- PostgreSQL ---
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
PG_USER = os.getenv("POSTGRES_USER", "user")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
PG_DB = os.getenv("POSTGRES_DB", "db")

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=PG_HOST,
    port=PG_PORT,
    user=PG_USER,
    password=PG_PASSWORD,
    dbname=PG_DB,
)


# --- Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
)

# --- FastAPI ---
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class ApartmentCreate(BaseModel):
    listing_id: str
    name: str
    price: float  # stored as NUMERIC(12,2) in DB; we cast to float for API
    poi: Optional[Dict[str, Any]] = None


class Apartment(ApartmentCreate):
    id: int


# --- Helpers ---
def _to_jsonable(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


@contextmanager
def get_db_connection():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        # Do NOT close a pooled connection; return it to the pool
        pool.putconn(conn)


def fetch_from_db(query: str, params=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# --- Endpoints ---
@app.get("/apartments", response_model=List[Apartment])
async def get_apartments():
    try:
        cache_key = "apartments:all"
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)

        result = fetch_from_db("SELECT id, listing_id, name, price, poi FROM apartments")
        if result:
            # Ensure Decimals and other types are JSON-safe for Redis cache
            r.set(cache_key, json.dumps(_to_jsonable(result)), ex=60)
        return result
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/apartments/{apartment_id}", response_model=Apartment)
async def get_apartment(apartment_id: int):
    try:
        cache_key = f"apartments:{apartment_id}"
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)

        result = fetch_from_db(
            "SELECT id, listing_id, name, price, poi FROM apartments WHERE id = %s",
            (apartment_id,),
        )
        if not result:
            raise HTTPException(status_code=404, detail="Apartment not found")

        r.set(cache_key, json.dumps(_to_jsonable(result[0])), ex=60)
        return result[0]
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/apartments", response_model=Apartment)
async def create_apartment(apartment: ApartmentCreate):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO apartments (listing_id, name, price, poi)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, listing_id, name, price, poi
                    """,
                    (
                        apartment.listing_id,
                        apartment.name,
                        apartment.price,
                        Json(apartment.poi) if apartment.poi is not None else None,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=500, detail="Failed to create apartment")
                conn.commit()
                result = dict(row)

        try:
            r.delete("apartments:all")
        except redis.RedisError:
            pass

        return result
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.put("/apartments/{apartment_id}", response_model=Apartment)
async def update_apartment(apartment_id: int, apartment: ApartmentCreate):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE apartments
                    SET listing_id = %s, name = %s, price = %s, poi = %s
                    WHERE id = %s
                    RETURNING id, listing_id, name, price, poi
                    """,
                    (
                        apartment.listing_id,
                        apartment.name,
                        apartment.price,
                        Json(apartment.poi) if apartment.poi is not None else None,
                        apartment_id,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Apartment not found")
                conn.commit()
                result = dict(row)

        try:
            r.delete(f"apartments:{apartment_id}")
            r.delete("apartments:all")
        except redis.RedisError:
            pass

        return result
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.delete("/apartments/{apartment_id}")
async def delete_apartment(apartment_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "DELETE FROM apartments WHERE id = %s RETURNING id",
                    (apartment_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Apartment not found")
                conn.commit()

        try:
            r.delete(f"apartments:{apartment_id}")
            r.delete("apartments:all")
        except redis.RedisError:
            pass

        return {"detail": "Apartment deleted"}
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.on_event("startup")
async def startup_event():
    # Test database connection
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

    # Test Redis connection
    try:
        r.ping()
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    pool.closeall()
    try:
        r.close()
    except Exception:
        pass