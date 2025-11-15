

from typing import Optional, Dict, Any, List

from .models import Apartment


def parse_geotext(s: Optional[str]) -> Optional[Dict[str, float]]:
    if not s:
        return None
    try:
        if isinstance(s, str) and s.upper().startswith("SRID="):
            s = s.split(";", 1)[1]
        if isinstance(s, str) and s.upper().startswith("POINT(") and s.endswith(")"):
            inside = s[s.find("(") + 1 : -1].strip()
            parts = inside.split()
            if len(parts) >= 2:
                lng = float(parts[0]); lat = float(parts[1])
                return {"lat": lat, "lng": lng}
    except Exception:
        pass
    return None


def serialize_apartment(obj: Apartment, geotext: Optional[str] = None, photos: Optional[List[int]] = None, pois: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    fields = [
        "id","source_website","source_id","source_url","price","currency","room_num",
        "footage","price_per_m2","city","description","photo_attractiveness",
        "student_attractiveness","single_attractiveness","dog_owner_attractiveness",
        "universal_attractiveness","family_attractiveness","poi_desc","price_desc",
        "size_desc",
    ]
    data: Dict[str, Any] = {}
    for f in fields:
        data[f] = getattr(obj, f, None)
    data["id"] = getattr(obj, "id", None)

    data["geolocation"] = parse_geotext(geotext)

    # photos: prefer explicit list
    if photos is not None:
        data["photo_ids"] = photos
    else:
        data["photo_ids"] = [p.id for p in getattr(obj, "photos", [])] if getattr(obj, "photos", None) is not None else []

    # pois: prefer explicit list
    if pois is not None:
        data["pois"] = pois
    else:
        pois_out = []
        for rel in getattr(obj, "pois", []) or []:
            poi = getattr(rel, "poi", None)
            if not poi:
                continue
            poi_geo = parse_geotext(str(getattr(poi, "geolocation", None)))
            category = getattr(rel, "category", None)
            cat_val = category.value if hasattr(category, "value") else category
            pois_out.append({"id": getattr(poi, "id", None), "name": getattr(poi, "name", None), "category": cat_val, "geolocation": poi_geo})
        data["pois"] = pois_out

    return data