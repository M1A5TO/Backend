from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel



class GeoPoint(BaseModel):
    lat: float
    lng: float

class POIOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    geolocation: Optional[GeoPoint] = None
    class Config:
        from_attributes = True


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
    geolocation: Optional[GeoPoint] = None
    photo_attractiveness: Optional[int] = None
    student_attractiveness: Optional[int] = None
    single_attractiveness: Optional[int] = None
    dog_owner_attractiveness: Optional[int] = None
    universal_attractiveness: Optional[int] = None
    family_attractiveness: Optional[int] = None
    poi_desc: Optional[str] = None
    price_desc: Optional[str] = None
    size_desc: Optional[str] = None


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


class ApartmentOut(BaseModel):
    id: int
    source_website: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    room_num: Optional[int] = None
    footage: Optional[Decimal] = None
    price_per_m2: Optional[Decimal] = None
    city: Optional[str] = None
    description: Optional[str] = None
    geolocation: Optional[GeoPoint] = None
    photo_attractiveness: Optional[int] = None
    student_attractiveness: Optional[int] = None
    single_attractiveness: Optional[int] = None
    dog_owner_attractiveness: Optional[int] = None
    universal_attractiveness: Optional[int] = None
    family_attractiveness: Optional[int] = None
    poi_desc: Optional[str] = None
    price_desc: Optional[str] = None
    size_desc: Optional[str] = None

    photo_ids: List[int] = []
    pois: List[POIOut] = []

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


# --- POI Schemas ---
class POIBase(BaseModel):
    name: str
    category: str
    geolocation: GeoPoint


class POICreate(POIBase):
    pass


class POIUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    geolocation: Optional[GeoPoint] = None


class POIOut(BaseModel):
    id: int
    name: str
    category: str
    geolocation: Optional[GeoPoint] = None

    class Config:
        from_attributes = True


# --- ApartmentPOI Schemas ---
class ApartmentPOICreate(BaseModel):
    poi_id: int
    category: str


class ApartmentPOIOut(BaseModel):
    apartment_id: int
    poi_id: int
    category: str
    poi: Optional[POIOut] = None

    class Config:
        from_attributes = True