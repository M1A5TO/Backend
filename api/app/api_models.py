from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, ConfigDict



class GeoPoint(BaseModel):
    lat: float
    lng: float


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


class ApartmentExistsResponse(BaseModel):
    """Informacja czy mieszkanie o zadanym source_website + source_id istnieje w bazie."""
    exists: bool
    id: Optional[int] = None


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
    style: Optional[str] = None

    photo_ids: List[int] = []
    pois: List["POIOut"] = []

    model_config = ConfigDict(from_attributes=True)


class PhotoBase(BaseModel):
    apartment_id: int
    link: str
    style: Optional[str] = None
    room_type: Optional[str] = None
    room_style: Optional[str] = None
    photo_type: Optional[str] = None


class PhotoCreate(PhotoBase):
    pass


class PhotoUpdate(BaseModel):
    apartment_id: Optional[int] = None
    link: Optional[str] = None
    style: Optional[str] = None
    room_type: Optional[str] = None
    room_style: Optional[str] = None
    photo_type: Optional[str] = None


class PhotoOut(PhotoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- POI Schemas ---
class POIBase(BaseModel):
    category: str
    geolocation: GeoPoint


class POICreate(POIBase):
    pass


class POIUpdate(BaseModel):
    category: Optional[str] = None
    geolocation: Optional[GeoPoint] = None


class POIOut(BaseModel):
    id: int
    category: str
    geolocation: Optional[GeoPoint] = None

    model_config = ConfigDict(from_attributes=True)


# --- ApartmentPOI Schemas ---
class ApartmentPOICreate(BaseModel):
    poi_id: int
    time_to_poi: Optional[int] = None


class ApartmentPOIOut(BaseModel):
    apartment_id: int
    poi_id: int
    time_to_poi: Optional[int] = None
    poi: Optional[POIOut] = None

class CityOut(BaseModel):
    city: str

    model_config = ConfigDict(from_attributes=True)