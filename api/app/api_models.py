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


class BoundingBox(BaseModel):
    south_west: GeoPoint
    north_east: GeoPoint

    def to_polygon_wkt(self) -> str:
        sw = self.south_west
        ne = self.north_east
        coords = [
            (sw.lng, sw.lat),
            (sw.lng, ne.lat),
            (ne.lng, ne.lat),
            (ne.lng, sw.lat),
            (sw.lng, sw.lat),
        ]
        coord_str = ", ".join(f"{lng} {lat}" for lng, lat in coords)
        return f"SRID=4326;POLYGON(({coord_str}))"


class DuplicateCheckRequest(BaseModel):
    center: Optional[GeoPoint] = None
    radius_m: Optional[float] = None
    bounding_box: Optional[BoundingBox] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    footage_min: Optional[Decimal] = None
    footage_max: Optional[Decimal] = None
    limit: int = 50


class DuplicateCheckResponse(BaseModel):
    has_matches: bool
    count: int
    matches: List["ApartmentOut"]


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