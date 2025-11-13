import os
import json
import redis
import psycopg2
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor, Json

from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import uuid
import mimetypes

from .db import get_db_session, ensure_database
from .models import Apartment, Photo
from .common import optimize_image_to_webp



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


# --- Startup: ensure DB tables/migrations ---
@app.on_event("startup")
def on_startup():
    ensure_database()
    # Ensure media directory exists
    os.makedirs(os.getenv("MEDIA_ROOT", "/media/photos"), exist_ok=True)


# --- Schemas ---
class ApartmentBase(BaseModel):
    source_website: str
    source_id: str
    source_url: str
    price: Optional[Decimal] = None
    currency: Optional[str] = "PLN"
    room_num: Optional[int] = None
    footage: Optional[Decimal] = None
    price_per_m2: Optional[Decimal] = None
    city: Optional[str] = None
    description: Optional[str] = None
    photo_attractiveness: Optional[int] = None
    student_attractiveness: Optional[int] = None
    single_attractiveness: Optional[int] = None
    dog_owner_attractiveness: Optional[int] = None
    universal_attractiveness: Optional[int] = None
    family_attractiveness: Optional[int] = None
    poi_desc: Optional[str] = None
    price_desc: Optional[str] = None
    size_desc: Optional[str] = None
    style: Optional[str] = None


class ApartmentCreate(ApartmentBase):
    pass


class ApartmentUpdate(BaseModel):
    source_url: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    room_num: Optional[int] = None
    footage: Optional[Decimal] = None
    price_per_m2: Optional[Decimal] = None
    city: Optional[str] = None
    description: Optional[str] = None
    photo_attractiveness: Optional[int] = None
    student_attractiveness: Optional[int] = None
    single_attractiveness: Optional[int] = None
    dog_owner_attractiveness: Optional[int] = None
    universal_attractiveness: Optional[int] = None
    family_attractiveness: Optional[int] = None
    poi_desc: Optional[str] = None
    price_desc: Optional[str] = None
    size_desc: Optional[str] = None
    style: Optional[str] = None


class ApartmentOut(ApartmentBase):
    id: int

    class Config:
        from_attributes = True


class PhotoBase(BaseModel):
    apartment_id: int


class PhotoCreate(PhotoBase):
    pass


class PhotoUpdate(BaseModel):
    path: Optional[str] = None


class PhotoOut(PhotoBase):
    id: int

    class Config:
        from_attributes = True


# --- CRUD: Apartments ---
@app.get("/apartments", response_model=List[ApartmentOut])
def list_apartments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return db.query(Apartment).offset(skip).limit(limit).all()


@app.get("/apartments/{apartment_id}", response_model=ApartmentOut)
def get_apartment(apartment_id: int, db: Session = Depends(get_db_session)):
    obj = db.query(Apartment).get(apartment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Apartment not found")
    return obj


@app.post("/apartments", response_model=ApartmentOut, status_code=201)
def create_apartment(payload: ApartmentCreate, db: Session = Depends(get_db_session)):
    obj = Apartment(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.put("/apartments/{apartment_id}", response_model=ApartmentOut)
def update_apartment(apartment_id: int, payload: ApartmentUpdate, db: Session = Depends(get_db_session)):
    obj = db.query(Apartment).get(apartment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Apartment not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/apartments/{apartment_id}", status_code=204)
def delete_apartment(apartment_id: int, db: Session = Depends(get_db_session)):
    obj = db.query(Apartment).get(apartment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Apartment not found")
    db.delete(obj)
    db.commit()
    return None


# --- CRUD: Photos ---
@app.get("/photos", response_model=List[PhotoOut])
def list_photos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return db.query(Photo).offset(skip).limit(limit).all()


@app.get("/photos/{photo_id}")
def get_photo(photo_id: int, db: Session = Depends(get_db_session)):
    obj = db.query(Photo).get(photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    if not obj.path or not os.path.isfile(obj.path):
        raise HTTPException(status_code=404, detail="Photo file missing")
    media_type = mimetypes.guess_type(obj.path)[0] or "application/octet-stream"
    return FileResponse(path=obj.path, media_type=media_type)


@app.post("/photos", status_code=201)
async def create_photo(
    apartment_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    # Persist file in /media/photos/{apartment_id}/{index}{ext}
    media_root = os.getenv("MEDIA_ROOT", "/media/photos")
    apartment_dir = os.path.join(media_root, str(apartment_id))
    os.makedirs(apartment_dir, exist_ok=True)

    existing = [f for f in os.listdir(apartment_dir) if os.path.isfile(os.path.join(apartment_dir, f))]
    indices = []
    for name in existing:
        base, _ext = os.path.splitext(name)
        try:
            indices.append(int(base))
        except ValueError:
            continue
    next_index = (max(indices) + 1) if indices else 0

    ext = os.path.splitext(file.filename or "")[1] or ""
    base_path = os.path.join(apartment_dir, f"{next_index}")
    temp_path = base_path + ext

    try:
        with open(temp_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    finally:
        await file.close()

    # Optimize to webp; returns final path or None
    optimized_path = optimize_image_to_webp(temp_path)
    if not optimized_path:
        # cleanup
        try:
            if os.path.isfile(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Invalid image or optimization failed")

    obj = Photo(apartment_id=apartment_id, path=optimized_path)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id, "apartment_id": obj.apartment_id}


@app.put("/photos/{photo_id}")
async def update_photo(
    photo_id: int,
    apartment_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db_session),
):
    obj = db.query(Photo).get(photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Update apartment relation if provided
    if apartment_id is not None:
        obj.apartment_id = apartment_id

    # Replace file if provided
    if file is not None:
        media_root = os.getenv("MEDIA_ROOT", "/media/photos")
        apartment_dir = os.path.join(media_root, str(obj.apartment_id))
        os.makedirs(apartment_dir, exist_ok=True)

        existing = [f for f in os.listdir(apartment_dir) if os.path.isfile(os.path.join(apartment_dir, f))]
        indices = []
        for name in existing:
            base, _ext = os.path.splitext(name)
            try:
                indices.append(int(base))
            except ValueError:
                continue
        next_index = (max(indices) + 1) if indices else 0

        ext = os.path.splitext(file.filename or "")[1] or ""
        base_path = os.path.join(apartment_dir, f"{next_index}")
        temp_path = base_path + ext

        try:
            with open(temp_path, "wb") as out:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
        finally:
           await file.close()

        optimized_path = optimize_image_to_webp(temp_path)
        if not optimized_path:
            try:
                if os.path.isfile(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            raise HTTPException(status_code=400, detail="Invalid image or optimization failed")

        # Remove old file if exists
        try:
            if obj.path and os.path.isfile(obj.path):
                os.remove(obj.path)
        except Exception:
            pass

        obj.path = optimized_path

    db.commit()
    return {"id": obj.id, "apartment_id": obj.apartment_id}


@app.delete("/photos/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Session = Depends(get_db_session)):
    obj = db.query(Photo).get(photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(obj)
    db.commit()
    return None

