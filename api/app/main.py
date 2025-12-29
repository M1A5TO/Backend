import os
from pathlib import Path
from dotenv import load_dotenv
import redis
from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from contextlib import asynccontextmanager
from sqlalchemy import func, text


project_root = Path(__file__).resolve().parents[2]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from .db import get_db_session, ensure_database
from .models import Apartment, Photo, POI, ApartmentPOI


from .api_models import (
    ApartmentOut, ApartmentCreate, ApartmentUpdate, PhotoOut, PhotoCreate, PhotoUpdate,
    POIOut, POICreate, POIUpdate,
    ApartmentPOIOut, ApartmentPOICreate,
    DuplicateCheckRequest, DuplicateCheckResponse
)
from .helpers import serialize_apartment, parse_geotext

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database()
    os.makedirs(os.getenv("MEDIA_ROOT", "/media/photos"), exist_ok=True)
    yield   


# --- FastAPI ---
app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- CRUD: Apartments ---

@app.get("/apartments", response_model=List[ApartmentOut])
def list_apartments(
    city: Optional[str] = None,
    profile: Optional[str] = None,
    max_price: Optional[float] = None,
    min_footage: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """
    List apartments with optional filtering.
    
    - **city**: Filter by city name
    - **profile**: Filter by user profile (student, single, dog_owner, family, universal)
    - **max_price**: Maximum price filter
    - **min_footage**: Minimum footage (m²) filter
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    query = db.query(Apartment, func.ST_AsText(Apartment.geolocation).label("geotext")).options(
        joinedload(Apartment.photos),
        joinedload(Apartment.pois).joinedload(ApartmentPOI.poi),
    )
    
    if city:
        query = query.filter(Apartment.city.ilike(f"%{city}%"))
    
    if max_price is not None:
        query = query.filter(Apartment.price <= max_price)
    
    if min_footage is not None:
        query = query.filter(Apartment.footage >= min_footage)

    if profile:
        profile_lower = profile.lower()
        if profile_lower == "student":
            query = query.order_by(Apartment.student_attractiveness.desc().nulls_last())
        elif profile_lower == "single":
            query = query.order_by(Apartment.single_attractiveness.desc().nulls_last())
        elif profile_lower == "dog_owner":
            query = query.order_by(Apartment.dog_owner_attractiveness.desc().nulls_last())
        elif profile_lower == "family":
            query = query.order_by(Apartment.family_attractiveness.desc().nulls_last())
        elif profile_lower == "universal":
            query = query.order_by(Apartment.universal_attractiveness.desc().nulls_last())
        else:
            query = query.order_by(Apartment.universal_attractiveness.desc().nulls_last())
    else:
        query = query.order_by(Apartment.universal_attractiveness.desc().nulls_last())

    rows = query.offset(skip).limit(limit).all()
    
    result = []
    for apt, geotext in rows:
        photos = [p.id for p in getattr(apt, "photos", [])]
        pois = []
        for rel in getattr(apt, "pois", []) or []:
            poi = getattr(rel, "poi", None)
            if not poi:
                continue
            poi_geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
            poi_geo = parse_geotext(poi_geotext)
            cat_val = poi.category.value if hasattr(poi.category, "value") else str(poi.category)
            pois.append({"id": poi.id, "category": cat_val, "geolocation": poi_geo, "time_to_poi": rel.time_to_poi})
        result.append(serialize_apartment(apt, geotext, photos=photos, pois=pois))
    return result


@app.get("/apartments/cities", response_model=List[str])
def list_apartment_cities(db: Session = Depends(get_db_session), username: str = Depends(verify_token)):
    """
    Get all unique cities from apartments table.
    """
    query = db.query(Apartment.city).distinct().filter(Apartment.city.isnot(None)).order_by(Apartment.city)
    cities = [row[0] for row in query.all()]
    return cities


@app.get("/apartments/{apartment_id}", response_model=ApartmentOut)
def get_apartment(apartment_id: int, db: Session = Depends(get_db_session)):
    row = (
        db.query(Apartment, func.ST_AsText(Apartment.geolocation).label("geotext"))
        .options(
            joinedload(Apartment.photos),
            joinedload(Apartment.pois).joinedload(ApartmentPOI.poi),
        )
        .filter(Apartment.id == apartment_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Apartment not found")
    apt, geotext = row
    photos = [p.id for p in getattr(apt, "photos", [])]
    pois = []
    for rel in getattr(apt, "pois", []) or []:
        poi = getattr(rel, "poi", None)
        if not poi:
            continue
        poi_geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
        poi_geo = parse_geotext(poi_geotext)
        cat_val = poi.category.value if hasattr(poi.category, "value") else str(poi.category)
        pois.append({"id": poi.id, "category": cat_val, "geolocation": poi_geo})
    return serialize_apartment(apt, geotext, photos=photos, pois=pois)

@app.post("/apartments", response_model=ApartmentOut, status_code=201)
def create_apartment(payload: ApartmentCreate, db: Session = Depends(get_db_session)):
    from .models import ApartmentStyle
    
    data = payload.model_dump(exclude={"geolocation", "style"})
    obj = Apartment(**data)
    
    if payload.style is not None:
        try:
            obj.style = ApartmentStyle(payload.style)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid style. Must be one of: {[s.value for s in ApartmentStyle]}")
    
    if payload.geolocation is not None:
        obj.geolocation = f"SRID=4326;POINT({payload.geolocation.lng} {payload.geolocation.lat})"
    db.add(obj)
    db.commit()
    db.refresh(obj)
    geotext = db.query(func.ST_AsText(Apartment.geolocation)).filter(Apartment.id == obj.id).scalar()
    return serialize_apartment(obj, geotext, photos=[], pois=[])


@app.put("/apartments/{apartment_id}", response_model=ApartmentOut)
def update_apartment(apartment_id: int, payload: ApartmentUpdate, db: Session = Depends(get_db_session)):
    from .models import ApartmentStyle
    
    obj = db.get(Apartment, apartment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Apartment not found")
    update_data = payload.model_dump(exclude_unset=True, exclude={"geolocation", "style"})
    for k, v in update_data.items():
        setattr(obj, k, v)
    
    if payload.style is not None:
        try:
            obj.style = ApartmentStyle(payload.style)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid style. Must be one of: {[s.value for s in ApartmentStyle]}")
    elif hasattr(payload, "style") and payload.style == "":
        obj.style = None
    
    if getattr(payload, "geolocation", None) is not None:
        geo = payload.geolocation
        if geo is None:
            obj.geolocation = None
        else:
            obj.geolocation = f"SRID=4326;POINT({geo.lng} {geo.lat})"
    db.commit()
    db.refresh(obj)
    geotext = db.query(func.ST_AsText(Apartment.geolocation)).filter(Apartment.id == obj.id).scalar()
    photos = [p.id for p in getattr(obj, "photos", [])]
    pois = []
    for rel in getattr(obj, "pois", []) or []:
        poi = getattr(rel, "poi", None)
        if not poi:
            continue
        poi_geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
        poi_geo = parse_geotext(poi_geotext)
        cat_val = poi.category.value if hasattr(poi.category, "value") else str(poi.category)
        pois.append({"id": poi.id, "category": cat_val, "geolocation": poi_geo})
    return serialize_apartment(obj, geotext, photos=photos, pois=pois)


@app.delete("/apartments/{apartment_id}", status_code=204)
def delete_apartment(apartment_id: int, db: Session = Depends(get_db_session)):
    obj = db.get(Apartment, apartment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Apartment not found")
    db.delete(obj)
    db.commit()
    return None


@app.post("/apartments/duplicates/check", response_model=DuplicateCheckResponse)
def check_apartment_duplicates(payload: DuplicateCheckRequest, db: Session = Depends(get_db_session)):
    result = db.execute(text("SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = 4326;"))
    if result.scalar() == 0:
        db.execute(text("""
            INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext)
            VALUES (4326, 'EPSG', 4326, 
                '+proj=longlat +datum=WGS84 +no_defs',
                'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
            ) ON CONFLICT (srid) DO NOTHING;
        """))
        db.commit()
    
    if payload.limit <= 0 or payload.limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    if payload.center is None and payload.radius_m is not None:
        raise HTTPException(status_code=400, detail="center is required when radius_m is provided")
    if payload.radius_m is None and payload.center is not None:
        raise HTTPException(status_code=400, detail="radius_m is required when center is provided")

    if not payload.bounding_box and not payload.center:
        raise HTTPException(status_code=400, detail="Provide either center+radius_m or bounding_box")
    query = db.query(
        Apartment,
        func.ST_AsText(Apartment.geolocation).label("geotext")
    ).filter(Apartment.geolocation.isnot(None))

    if payload.price_min is not None:
        query = query.filter(Apartment.price >= payload.price_min)
    if payload.price_max is not None:
        query = query.filter(Apartment.price <= payload.price_max)
    if payload.footage_min is not None:
        query = query.filter(Apartment.footage >= payload.footage_min)
    if payload.footage_max is not None:
        query = query.filter(Apartment.footage <= payload.footage_max)

    if payload.center and payload.radius_m:
        point_geog = text(
            f"ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography"
        ).bindparams(lng=payload.center.lng, lat=payload.center.lat)
        query = query.filter(
            func.ST_DWithin(
                Apartment.geolocation,
                point_geog,
                payload.radius_m
            )
        )

    if payload.bounding_box:
        poly_wkt = payload.bounding_box.to_polygon_wkt()
        poly_wkt_clean = poly_wkt.replace('SRID=4326;', '') if 'SRID=4326;' in poly_wkt else poly_wkt
        if 'SRID=' in poly_wkt:
            poly_geom = text(f"ST_GeomFromEWKT(:poly_wkt)").bindparams(poly_wkt=poly_wkt)
        else:
            poly_geom = text(f"ST_SetSRID(ST_GeomFromText(:poly_wkt), 4326)").bindparams(poly_wkt=poly_wkt_clean)
        apt_geom = func.ST_SetSRID(
            func.ST_GeomFromWKB(func.ST_AsBinary(Apartment.geolocation)),
            4326
        )
        query = query.filter(
            func.ST_Within(
                apt_geom,
                poly_geom
            )
        )

    rows = query.limit(payload.limit).all()
    
    matches = [
        serialize_apartment(apartment, geotext)
        for apartment, geotext in rows
    ]
    return DuplicateCheckResponse(
        has_matches=bool(matches),
        count=len(matches),
        matches=matches,
    )


# --- CRUD: Photos ---
@app.get("/photos", response_model=List[PhotoOut])
def list_photos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return db.query(Photo).offset(skip).limit(limit).all()


@app.get("/photos/{photo_id}", response_model=PhotoOut)
def get_photo(photo_id: int, db: Session = Depends(get_db_session)):
    obj = db.get(Photo, photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    return obj


@app.post("/photos", response_model=PhotoOut, status_code=201)
def create_photo(payload: PhotoCreate, db: Session = Depends(get_db_session)):
    """Create a new photo with a link."""
    from .models import ApartmentStyle, RoomType, RoomStyle
    
    style_enum = None
    room_type_enum = None
    room_style_enum = None

    if payload.style is not None:
        try:
            style_enum = ApartmentStyle(payload.style)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid style. Must be one of: {[s.value for s in ApartmentStyle]}")
    
    if payload.room_type is not None:
        try:
            room_type_enum = RoomType(payload.room_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid room_type. Must be one of: {[r.value for r in RoomType]}")

    if payload.room_style is not None:
        try:
            room_style_enum = RoomStyle(payload.room_style)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid room_style. Must be one of: {[r.value for r in RoomStyle]}")
    
    obj = Photo(
        apartment_id=payload.apartment_id,
        link=payload.link,
        style=style_enum,
        room_type=room_type_enum,
        room_style=room_style_enum,
        photo_type=payload.photo_type,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.put("/photos/{photo_id}", response_model=PhotoOut)
def update_photo(
    photo_id: int,
    payload: PhotoUpdate,
    db: Session = Depends(get_db_session),
):
    """Update photo link and/or style."""
    from .models import ApartmentStyle, RoomType, RoomStyle
    
    obj = db.get(Photo, photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")

    if payload.apartment_id is not None:
        obj.apartment_id = payload.apartment_id

    if payload.link is not None:
        obj.link = payload.link

    if payload.style is not None:
        if payload.style == "":
            obj.style = None
        else:
            try:
                obj.style = ApartmentStyle(payload.style)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid style. Must be one of: {[s.value for s in ApartmentStyle]}")

    if payload.room_type is not None:
        if payload.room_type == "":
            obj.room_type = None
        else:
            try:
                obj.room_type = RoomType(payload.room_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid room_type. Must be one of: {[r.value for r in RoomType]}")

    if payload.room_style is not None:
        if payload.room_style == "":
            obj.room_style = None
        else:
            try:
                obj.room_style = RoomStyle(payload.room_style)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid room_style. Must be one of: {[r.value for r in RoomStyle]}")

    if payload.photo_type is not None:
        obj.photo_type = payload.photo_type

    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/photos/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Session = Depends(get_db_session)):
    obj = db.get(Photo, photo_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(obj)
    db.commit()
    return None


# --- CRUD: POIs ---
@app.get("/pois", response_model=List[POIOut])
def list_pois(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    rows = db.query(POI, func.ST_AsText(POI.geolocation).label("geotext")).offset(skip).limit(limit).all()
    result = []
    for poi, geotext in rows:
        result.append({
            "id": poi.id,
            "category": poi.category.value if hasattr(poi.category, "value") else str(poi.category),
            "geolocation": parse_geotext(geotext)
        })
    return result


@app.get("/pois/{poi_id}", response_model=POIOut)
def get_poi(poi_id: int, db: Session = Depends(get_db_session)):
    row = db.query(POI, func.ST_AsText(POI.geolocation).label("geotext")).filter(POI.id == poi_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="POI not found")
    poi, geotext = row
    return {
        "id": poi.id,
        "category": poi.category.value if hasattr(poi.category, "value") else str(poi.category),
        "geolocation": parse_geotext(geotext)
    }


@app.post("/pois", response_model=POIOut, status_code=201)
def create_poi(payload: POICreate, db: Session = Depends(get_db_session)):
    from .models import POICategory
    
    try:
        category_enum = POICategory(payload.category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {[c.value for c in POICategory]}")
    
    poi = POI(
        category=category_enum,
        geolocation=f"SRID=4326;POINT({payload.geolocation.lng} {payload.geolocation.lat})"
    )
    db.add(poi)
    db.commit()
    db.refresh(poi)
    geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
    return {
        "id": poi.id,
        "category": poi.category.value,
        "geolocation": parse_geotext(geotext)
    }


@app.put("/pois/{poi_id}", response_model=POIOut)
def update_poi(poi_id: int, payload: POIUpdate, db: Session = Depends(get_db_session)):
    from .models import POICategory
    
    poi = db.get(POI, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    if payload.category is not None:
        try:
            poi.category = POICategory(payload.category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {[c.value for c in POICategory]}")
    if payload.geolocation is not None:
        poi.geolocation = f"SRID=4326;POINT({payload.geolocation.lng} {payload.geolocation.lat})"
    
    db.commit()
    db.refresh(poi)
    geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
    return {
        "id": poi.id,
        "category": poi.category.value,
        "geolocation": parse_geotext(geotext)
    }


@app.delete("/pois/{poi_id}", status_code=204)
def delete_poi(poi_id: int, db: Session = Depends(get_db_session)):
    poi = db.get(POI, poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    db.delete(poi)
    db.commit()
    return None


# --- CRUD: Apartment Best POIs ---
@app.get("/apartments/{apartment_id}/pois", response_model=List[ApartmentPOIOut])
def list_apartment_pois(apartment_id: int, db: Session = Depends(get_db_session)):
    apartment = db.get(Apartment, apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    rels = db.query(ApartmentPOI).filter(ApartmentPOI.apartment_id == apartment_id).all()
    result = []
    for rel in rels:
        poi = db.get(POI, rel.poi_id)
        if not poi:
            continue
        poi_geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
        result.append({
            "apartment_id": rel.apartment_id,
            "poi_id": rel.poi_id,
            "time_to_poi": rel.time_to_poi,
            "poi": {
                "id": poi.id,
                "category": poi.category.value if hasattr(poi.category, "value") else str(poi.category),
                "geolocation": parse_geotext(poi_geotext)
            }
        })
    return result


@app.post("/apartments/{apartment_id}/pois", response_model=ApartmentPOIOut, status_code=201)
def add_apartment_poi(apartment_id: int, payload: ApartmentPOICreate, db: Session = Depends(get_db_session)):
    apartment = db.get(Apartment, apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    poi = db.get(POI, payload.poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    
    existing = db.query(ApartmentPOI).filter(
        ApartmentPOI.apartment_id == apartment_id,
        ApartmentPOI.poi_id == payload.poi_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This POI is already assigned to this apartment")
    
    rel = ApartmentPOI(
        apartment_id=apartment_id,
        poi_id=payload.poi_id,
        time_to_poi=payload.time_to_poi
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    
    poi_geotext = db.query(func.ST_AsText(POI.geolocation)).filter(POI.id == poi.id).scalar()
    return {
        "apartment_id": rel.apartment_id,
        "poi_id": rel.poi_id,
        "time_to_poi": rel.time_to_poi,
        "poi": {
            "id": poi.id,
            "category": poi.category.value,
            "geolocation": parse_geotext(poi_geotext)
        }
    }


@app.delete("/apartments/{apartment_id}/pois/{poi_id}", status_code=204)
def remove_apartment_poi(apartment_id: int, poi_id: int, db: Session = Depends(get_db_session)):
    rel = db.query(ApartmentPOI).filter(
        ApartmentPOI.apartment_id == apartment_id,
        ApartmentPOI.poi_id == poi_id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Apartment-POI relation not found")
    db.delete(rel)
    db.commit()
    return None

