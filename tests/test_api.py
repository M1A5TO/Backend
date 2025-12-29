import io
import os


def test_apartment_crud_flow(client):
    """Test CREATE, GET, UPDATE, DELETE dla apartments z style"""
    # CREATE - utwórz mieszkanie
    payload = {
        "source_website": "otodom",
        "source_id": "T1",
        "source_url": "http://example.com/apt",
        "city": "Warsaw",
        "price": 2500.50,
        "footage": 45.5,
        "style": "modern"
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 201, r.text
    apt = r.json()
    apt_id = apt["id"]
    
    # Sprawdź czy wszystkie pola się zgadzają
    assert apt["city"] == "Warsaw"
    assert float(apt["price"]) == 2500.50
    assert float(apt["footage"]) == 45.5
    assert apt["style"] == "modern"
    assert apt["source_website"] == "otodom"
    assert apt["source_id"] == "T1"

    # GET - pobierz mieszkanie i sprawdź czy dane się zgadzają
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == apt_id
    assert data["city"] == "Warsaw"
    assert float(data["price"]) == 2500.50
    assert float(data["footage"]) == 45.5
    assert data["style"] == "modern"

    # LIST - sprawdź czy mieszkanie jest na liście
    r = client.get("/apartments?limit=5")
    assert r.status_code == 200
    assert any(a["id"] == apt_id for a in r.json())

    # UPDATE - zaktualizuj mieszkanie
    update_payload = {
        "city": "Krakow",
        "price": 3000.00,
        "style": "classic"
    }
    r = client.put(f"/apartments/{apt_id}", json=update_payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated["city"] == "Krakow"
    assert float(updated["price"]) == 3000.00
    assert updated["style"] == "classic"
    assert float(updated["footage"]) == 45.5  # Nie zmienione

    # GET - sprawdź czy update się zapisał
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["city"] == "Krakow"
    assert float(data["price"]) == 3000.00
    assert data["style"] == "classic"

    # DELETE
    r = client.delete(f"/apartments/{apt_id}")
    assert r.status_code == 204

    # GET - sprawdź czy mieszkanie zostało usunięte
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 404


def test_photo_create_get_update_delete(client):
    """Test CREATE, GET, UPDATE, DELETE dla photos z link i style"""
    # CREATE apartment dla photo
    apt_payload = {
        "source_website": "otodom",
        "source_id": "T2",
        "source_url": "http://example.com/apt2",
        "city": "Gdansk",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # CREATE photo z link i style
    photo_payload = {
        "apartment_id": apt_id,
        "link": "https://example.com/photo1.jpg",
        "style": "modern"
    }
    r = client.post("/photos", json=photo_payload)
    assert r.status_code == 201, r.text
    photo_data = r.json()
    photo_id = photo_data["id"]
    
    # Sprawdź czy wszystkie pola się zgadzają
    assert photo_data["apartment_id"] == apt_id
    assert photo_data["link"] == "https://example.com/photo1.jpg"
    assert photo_data["style"] == "modern"

    # GET - pobierz photo i sprawdź czy dane się zgadzają
    r = client.get(f"/photos/{photo_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == photo_id
    assert data["apartment_id"] == apt_id
    assert data["link"] == "https://example.com/photo1.jpg"
    assert data["style"] == "modern"

    # LIST - sprawdź czy photo jest na liście
    r = client.get("/photos")
    assert r.status_code == 200
    photos = r.json()
    assert any(p["id"] == photo_id for p in photos)

    # UPDATE - zaktualizuj photo
    update_payload = {
        "link": "https://example.com/photo1_updated.jpg",
        "style": "classic"
    }
    r = client.put(f"/photos/{photo_id}", json=update_payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated["link"] == "https://example.com/photo1_updated.jpg"
    assert updated["style"] == "classic"
    assert updated["apartment_id"] == apt_id  # Nie zmienione

    # GET - sprawdź czy update się zapisał
    r = client.get(f"/photos/{photo_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["link"] == "https://example.com/photo1_updated.jpg"
    assert data["style"] == "classic"

    # DELETE
    r = client.delete(f"/photos/{photo_id}")
    assert r.status_code == 204

    # GET - sprawdź czy photo zostało usunięte
    r = client.get(f"/photos/{photo_id}")
    assert r.status_code == 404

    # Cleanup
    client.delete(f"/apartments/{apt_id}")


def test_poi_create_get_update_delete(client):
    """Test CREATE, GET, UPDATE, DELETE dla POIs (bez name)"""
    # CREATE POI
    poi_payload = {
        "category": "supermarket",
        "geolocation": {
            "lat": 52.2297,
            "lng": 21.0122
        }
    }
    r = client.post("/pois", json=poi_payload)
    assert r.status_code == 201, r.text
    poi_data = r.json()
    poi_id = poi_data["id"]
    
    # Sprawdź czy wszystkie pola się zgadzają
    assert poi_data["category"] == "supermarket"
    assert poi_data["geolocation"]["lat"] == 52.2297
    assert poi_data["geolocation"]["lng"] == 21.0122
    # POI nie ma pola "name"
    assert "name" not in poi_data

    # GET - pobierz POI i sprawdź czy dane się zgadzają
    r = client.get(f"/pois/{poi_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == poi_id
    assert data["category"] == "supermarket"
    assert data["geolocation"]["lat"] == 52.2297
    assert data["geolocation"]["lng"] == 21.0122
    assert "name" not in data

    # LIST - sprawdź czy POI jest na liście
    r = client.get("/pois")
    assert r.status_code == 200
    pois = r.json()
    assert any(p["id"] == poi_id for p in pois)

    # UPDATE - zaktualizuj POI
    update_payload = {
        "category": "pharmacy",
        "geolocation": {
            "lat": 52.2300,
            "lng": 21.0130
        }
    }
    r = client.put(f"/pois/{poi_id}", json=update_payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated["category"] == "pharmacy"
    assert updated["geolocation"]["lat"] == 52.2300
    assert updated["geolocation"]["lng"] == 21.0130

    # GET - sprawdź czy update się zapisał
    r = client.get(f"/pois/{poi_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "pharmacy"
    assert data["geolocation"]["lat"] == 52.2300
    assert data["geolocation"]["lng"] == 21.0130

    # DELETE
    r = client.delete(f"/pois/{poi_id}")
    assert r.status_code == 204

    # GET - sprawdź czy POI zostało usunięte
    r = client.get(f"/pois/{poi_id}")
    assert r.status_code == 404


def test_apartment_poi_create_get_delete(client):
    """Test CREATE, GET, DELETE dla ApartmentPOI z time_to_poi"""
    # CREATE apartment
    apt_payload = {
        "source_website": "otodom",
        "source_id": "T3",
        "source_url": "http://example.com/apt3",
        "city": "Warsaw",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # CREATE POI
    poi_payload = {
        "category": "supermarket",
        "geolocation": {
            "lat": 52.2297,
            "lng": 21.0122
        }
    }
    r = client.post("/pois", json=poi_payload)
    assert r.status_code == 201
    poi_id = r.json()["id"]

    # CREATE ApartmentPOI z time_to_poi
    apt_poi_payload = {
        "poi_id": poi_id,
        "time_to_poi": 5
    }
    r = client.post(f"/apartments/{apt_id}/pois", json=apt_poi_payload)
    assert r.status_code == 201, r.text
    apt_poi_data = r.json()
    
    # Sprawdź czy wszystkie pola się zgadzają
    assert apt_poi_data["apartment_id"] == apt_id
    assert apt_poi_data["poi_id"] == poi_id
    assert apt_poi_data["time_to_poi"] == 5
    assert apt_poi_data["poi"] is not None
    assert apt_poi_data["poi"]["id"] == poi_id
    assert apt_poi_data["poi"]["category"] == "supermarket"
    # ApartmentPOI nie ma pola "category" - jest w poi
    assert "category" not in apt_poi_data or apt_poi_data.get("category") is None

    # GET - pobierz listę POIs dla apartment
    r = client.get(f"/apartments/{apt_id}/pois")
    assert r.status_code == 200
    pois_list = r.json()
    assert len(pois_list) == 1
    assert pois_list[0]["apartment_id"] == apt_id
    assert pois_list[0]["poi_id"] == poi_id
    assert pois_list[0]["time_to_poi"] == 5
    assert pois_list[0]["poi"]["category"] == "supermarket"

    # GET apartment - sprawdź czy POIs są w odpowiedzi
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 200
    apt_data = r.json()
    assert len(apt_data["pois"]) == 1
    assert apt_data["pois"][0]["id"] == poi_id
    assert apt_data["pois"][0]["category"] == "supermarket"
    # Sprawdź czy time_to_poi jest w odpowiedzi (może być w relacji)
    
    # UPDATE - zaktualizuj time_to_poi (przez usunięcie i dodanie ponownie)
    # Najpierw usuń
    r = client.delete(f"/apartments/{apt_id}/pois/{poi_id}")
    assert r.status_code == 204
    
    # Dodaj ponownie z nowym time_to_poi
    apt_poi_payload2 = {
        "poi_id": poi_id,
        "time_to_poi": 10
    }
    r = client.post(f"/apartments/{apt_id}/pois", json=apt_poi_payload2)
    assert r.status_code == 201
    updated_data = r.json()
    assert updated_data["time_to_poi"] == 10

    # GET - sprawdź czy update się zapisał
    r = client.get(f"/apartments/{apt_id}/pois")
    assert r.status_code == 200
    pois_list = r.json()
    assert pois_list[0]["time_to_poi"] == 10

    # DELETE
    r = client.delete(f"/apartments/{apt_id}/pois/{poi_id}")
    assert r.status_code == 204

    # GET - sprawdź czy ApartmentPOI zostało usunięte
    r = client.get(f"/apartments/{apt_id}/pois")
    assert r.status_code == 200
    pois_list = r.json()
    assert len(pois_list) == 0

    # Cleanup
    client.delete(f"/apartments/{apt_id}")
    client.delete(f"/pois/{poi_id}")


def test_apartment_with_photos_and_pois(client):
    """Test kompleksowy - apartment z photos i pois"""
    # CREATE apartment
    apt_payload = {
        "source_website": "otodom",
        "source_id": "T4",
        "source_url": "http://example.com/apt4",
        "city": "Warsaw",
        "style": "modern"
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # CREATE photos
    photo1_payload = {
        "apartment_id": apt_id,
        "link": "https://example.com/photo1.jpg",
        "style": "modern"
    }
    r = client.post("/photos", json=photo1_payload)
    assert r.status_code == 201
    photo1_id = r.json()["id"]

    photo2_payload = {
        "apartment_id": apt_id,
        "link": "https://example.com/photo2.jpg",
        "style": "classic"
    }
    r = client.post("/photos", json=photo2_payload)
    assert r.status_code == 201
    photo2_id = r.json()["id"]

    # CREATE POIs
    poi1_payload = {
        "category": "supermarket",
        "geolocation": {"lat": 52.2297, "lng": 21.0122}
    }
    r = client.post("/pois", json=poi1_payload)
    assert r.status_code == 201
    poi1_id = r.json()["id"]

    poi2_payload = {
        "category": "pharmacy",
        "geolocation": {"lat": 52.2300, "lng": 21.0130}
    }
    r = client.post("/pois", json=poi2_payload)
    assert r.status_code == 201
    poi2_id = r.json()["id"]

    # CREATE ApartmentPOIs
    r = client.post(f"/apartments/{apt_id}/pois", json={"poi_id": poi1_id, "time_to_poi": 5})
    assert r.status_code == 201
    r = client.post(f"/apartments/{apt_id}/pois", json={"poi_id": poi2_id, "time_to_poi": 10})
    assert r.status_code == 201

    # GET apartment - sprawdź czy wszystko się zgadza
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 200
    apt_data = r.json()
    
    assert apt_data["id"] == apt_id
    assert apt_data["style"] == "modern"
    assert len(apt_data["photo_ids"]) == 2
    assert photo1_id in apt_data["photo_ids"]
    assert photo2_id in apt_data["photo_ids"]
    assert len(apt_data["pois"]) == 2
    poi_ids = [p["id"] for p in apt_data["pois"]]
    assert poi1_id in poi_ids
    assert poi2_id in poi_ids

    # Sprawdź czy POIs mają poprawne kategorie
    for poi in apt_data["pois"]:
        assert poi["category"] in ["supermarket", "pharmacy"]
        assert "name" not in poi

    # Cleanup
    client.delete(f"/apartments/{apt_id}")
    client.delete(f"/pois/{poi1_id}")
    client.delete(f"/pois/{poi2_id}")


def test_duplicate_check_endpoint(client):
    """Test endpointu sprawdzającego duplikaty"""
    payload = {
        "source_website": "olx",
        "source_id": "DUP1",
        "source_url": "http://example.com/dup",
        "price": 3500,
        "footage": 40,
        "city": "Warsaw",
        "geolocation": {
            "lat": 52.2297,
            "lng": 21.0122
        }
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 201, r.text
    apt_id = r.json()["id"]

    # Test z center i radius
    body = {
        "center": {"lat": 52.2297, "lng": 21.0122},
        "radius_m": 150,
        "price_min": 3400,
        "price_max": 3600,
        "footage_min": 35,
        "footage_max": 45,
        "limit": 5
    }
    r = client.post("/apartments/duplicates/check", json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["has_matches"] is True
    assert data["count"] >= 1
    assert any(match["id"] == apt_id for match in data["matches"])

    # Test z bounding_box
    bbox_body = {
        "bounding_box": {
            "south_west": {"lat": 52.2290, "lng": 21.0115},
            "north_east": {"lat": 52.2305, "lng": 21.0130}
        },
        "price_min": 2000,
        "price_max": 4000,
        "footage_min": 35,
        "footage_max": 45,
    }
    r = client.post("/apartments/duplicates/check", json=bbox_body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] >= 1

    # Test bez dopasowań
    mismatch_body = {
        "center": {"lat": 52.2297, "lng": 21.0122},
        "radius_m": 50,
        "price_min": 100,
        "price_max": 200,
        "footage_min": 10,
        "footage_max": 15,
    }
    r = client.post("/apartments/duplicates/check", json=mismatch_body)
    assert r.status_code == 200, r.text
    assert r.json()["has_matches"] is False

    client.delete(f"/apartments/{apt_id}")


def test_apartment_validation_errors(client):
    """Test walidacji dla apartments - nieprawidłowe style, brakujące wymagane pola"""
    # Test z nieprawidłowym style
    payload = {
        "source_website": "otodom",
        "source_id": "V1",
        "source_url": "http://example.com/v1",
        "style": "invalid_style"
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 400
    assert "Invalid style" in r.json()["detail"]

    # Test z brakującymi wymaganymi polami
    payload = {
        "source_website": "otodom",
        # brak source_id i source_url
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 422  # Validation error

    # Test z nieprawidłowym style w update
    apt_payload = {
        "source_website": "otodom",
        "source_id": "V2",
        "source_url": "http://example.com/v2",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    update_payload = {"style": "invalid_style"}
    r = client.put(f"/apartments/{apt_id}", json=update_payload)
    assert r.status_code == 400
    assert "Invalid style" in r.json()["detail"]

    # Cleanup
    client.delete(f"/apartments/{apt_id}")


def test_apartment_list_filtering(client):
    """Test filtrowania w list_apartments"""
    # Utwórz kilka mieszkań z różnymi parametrami
    apts = []
    for i, city in enumerate(["Warsaw", "Krakow", "Warsaw"]):
        payload = {
            "source_website": "otodom",
            "source_id": f"FILT{i}",
            "source_url": f"http://example.com/filt{i}",
            "city": city,
            "price": 2000 + i * 500,
            "footage": 30 + i * 10,
        }
        r = client.post("/apartments", json=payload)
        assert r.status_code == 201
        apts.append(r.json()["id"])

    # Test filtrowania po city
    r = client.get("/apartments?city=Warsaw")
    assert r.status_code == 200
    results = r.json()
    assert all(apt["city"] == "Warsaw" for apt in results)
    assert any(apt["id"] == apts[0] for apt in results)
    assert any(apt["id"] == apts[2] for apt in results)

    # Test filtrowania po max_price
    r = client.get("/apartments?max_price=2500")
    assert r.status_code == 200
    results = r.json()
    assert all(float(apt.get("price", 0) or 0) <= 2500 for apt in results if apt.get("price"))

    # Test filtrowania po min_footage
    r = client.get("/apartments?min_footage=40")
    assert r.status_code == 200
    results = r.json()
    assert all(float(apt.get("footage", 0) or 0) >= 40 for apt in results if apt.get("footage"))

    # Cleanup
    for apt_id in apts:
        client.delete(f"/apartments/{apt_id}")


def test_apartment_cities_endpoint(client):
    """Test endpoint /apartments/cities"""
    # Utwórz kilka mieszkań z różnymi miastami
    cities = ["Warsaw", "Krakow", "Gdansk", "Warsaw"]  # Warsaw dwa razy, aby sprawdzić distinct
    apt_ids = []
    for i, city in enumerate(cities):
        payload = {
            "source_website": "otodom",
            "source_id": f"C{i}",
            "source_url": f"http://example.com/c{i}",
            "city": city,
            "price": 2000.0,
            "footage": 50.0
        }
        r = client.post("/apartments", json=payload)
        assert r.status_code == 201
        apt_ids.append(r.json()["id"])

    # Pobierz miasta
    r = client.get("/apartments/cities")
    assert r.status_code == 200
    result_cities = r.json()
    assert isinstance(result_cities, list)
    assert set(result_cities) == {"Gdansk", "Krakow", "Warsaw"}  # distinct, sorted
    assert result_cities == sorted(result_cities)  # posortowane

    # Cleanup
    for apt_id in apt_ids:
        client.delete(f"/apartments/{apt_id}")


def test_apartment_not_found_errors(client):
    """Test błędów 404 dla nieistniejących zasobów"""
    # GET nieistniejącego apartment
    r = client.get("/apartments/99999")
    assert r.status_code == 404

    # UPDATE nieistniejącego apartment
    r = client.put("/apartments/99999", json={"city": "Test"})
    assert r.status_code == 404

    # DELETE nieistniejącego apartment
    r = client.delete("/apartments/99999")
    assert r.status_code == 404

    # GET nieistniejącego photo
    r = client.get("/photos/99999")
    assert r.status_code == 404

    # GET nieistniejącego POI
    r = client.get("/pois/99999")
    assert r.status_code == 404


def test_photo_validation_errors(client):
    """Test walidacji dla photos"""
    # Utwórz apartment
    apt_payload = {
        "source_website": "otodom",
        "source_id": "PH1",
        "source_url": "http://example.com/ph1",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # Test z nieprawidłowym style
    photo_payload = {
        "apartment_id": apt_id,
        "link": "https://example.com/photo.jpg",
        "style": "invalid_style"
    }
    r = client.post("/photos", json=photo_payload)
    assert r.status_code == 400
    assert "Invalid style" in r.json()["detail"]

    # Cleanup
    client.delete(f"/apartments/{apt_id}")


def test_poi_validation_errors(client):
    """Test walidacji dla POIs"""
    # Test z nieprawidłową kategorią
    poi_payload = {
        "category": "invalid_category",
        "geolocation": {"lat": 52.2297, "lng": 21.0122}
    }
    r = client.post("/pois", json=poi_payload)
    assert r.status_code == 400
    assert "Invalid category" in r.json()["detail"]

    # Test z nieprawidłową kategorią w update
    poi_payload = {
        "category": "supermarket",
        "geolocation": {"lat": 52.2297, "lng": 21.0122}
    }
    r = client.post("/pois", json=poi_payload)
    assert r.status_code == 201
    poi_id = r.json()["id"]

    update_payload = {"category": "invalid_category"}
    r = client.put(f"/pois/{poi_id}", json=update_payload)
    assert r.status_code == 400
    assert "Invalid category" in r.json()["detail"]

    # Cleanup
    client.delete(f"/pois/{poi_id}")


def test_apartment_poi_duplicate_error(client):
    """Test próby dodania tego samego POI do apartment dwa razy"""
    # Utwórz apartment
    apt_payload = {
        "source_website": "otodom",
        "source_id": "DUP2",
        "source_url": "http://example.com/dup2",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # Utwórz POI
    poi_payload = {
        "category": "supermarket",
        "geolocation": {"lat": 52.2297, "lng": 21.0122}
    }
    r = client.post("/pois", json=poi_payload)
    assert r.status_code == 201
    poi_id = r.json()["id"]

    # Dodaj POI pierwszy raz
    apt_poi_payload = {"poi_id": poi_id, "time_to_poi": 5}
    r = client.post(f"/apartments/{apt_id}/pois", json=apt_poi_payload)
    assert r.status_code == 201

    # Próba dodania tego samego POI drugi raz
    r = client.post(f"/apartments/{apt_id}/pois", json=apt_poi_payload)
    assert r.status_code == 400
    assert "already assigned" in r.json()["detail"].lower()

    # Cleanup
    client.delete(f"/apartments/{apt_id}")
    client.delete(f"/pois/{poi_id}")


def test_apartment_poi_not_found_errors(client):
    """Test błędów 404 dla nieistniejących apartment/POI w relacjach"""
    # Utwórz apartment
    apt_payload = {
        "source_website": "otodom",
        "source_id": "NF1",
        "source_url": "http://example.com/nf1",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # Próba dodania nieistniejącego POI
    apt_poi_payload = {"poi_id": 99999, "time_to_poi": 5}
    r = client.post(f"/apartments/{apt_id}/pois", json=apt_poi_payload)
    assert r.status_code == 404

    # Próba dodania POI do nieistniejącego apartment
    poi_payload = {
        "category": "supermarket",
        "geolocation": {"lat": 52.2297, "lng": 21.0122}
    }
    r = client.post("/pois", json=poi_payload)
    assert r.status_code == 201
    poi_id = r.json()["id"]

    r = client.post("/apartments/99999/pois", json={"poi_id": poi_id})
    assert r.status_code == 404

    # Cleanup
    client.delete(f"/apartments/{apt_id}")
    client.delete(f"/pois/{poi_id}")


def test_all_apartment_styles(client):
    """Test wszystkich dostępnych stylów mieszkania"""
    styles = ["modern", "classic", "scandinavian", "minimalist", "vintage", "other"]
    
    for style in styles:
        payload = {
            "source_website": "otodom",
            "source_id": f"STYLE_{style}",
            "source_url": f"http://example.com/style_{style}",
            "style": style
        }
        r = client.post("/apartments", json=payload)
        assert r.status_code == 201, f"Failed for style: {style}"
        apt_id = r.json()["id"]
        assert r.json()["style"] == style
        
        # Cleanup
        client.delete(f"/apartments/{apt_id}")


def test_all_poi_categories(client):
    """Test wszystkich dostępnych kategorii POI"""
    categories = [
        "supermarket", "convenience", "bakery", "pet_shop",
        "pharmacy", "clinic_hospital", "parcel_locker", "university",
        "library", "nightclub", "school", "kinder_childcare",
        "veterinary", "pub", "fitness_centre", "playground", "park",
        "bus_stop", "tram_stop", "rail_station"
    ]
    
    for category in categories:
        poi_payload = {
            "category": category,
            "geolocation": {"lat": 52.2297, "lng": 21.0122}
        }
        r = client.post("/pois", json=poi_payload)
        assert r.status_code == 201, f"Failed for category: {category}"
        poi_id = r.json()["id"]
        assert r.json()["category"] == category
        
        # Cleanup
        client.delete(f"/pois/{poi_id}")


def test_apartment_with_geolocation(client):
    """Test mieszkania z geolocation"""
    payload = {
        "source_website": "otodom",
        "source_id": "GEO1",
        "source_url": "http://example.com/geo1",
        "city": "Warsaw",
        "geolocation": {
            "lat": 52.2297,
            "lng": 21.0122
        }
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]
    
    # Sprawdź czy geolocation jest zapisane
    assert r.json()["geolocation"] is not None
    assert r.json()["geolocation"]["lat"] == 52.2297
    assert r.json()["geolocation"]["lng"] == 21.0122

    # GET i sprawdź geolocation
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 200
    assert r.json()["geolocation"]["lat"] == 52.2297
    assert r.json()["geolocation"]["lng"] == 21.0122

    # UPDATE geolocation
    update_payload = {
        "geolocation": {
            "lat": 52.2300,
            "lng": 21.0130
        }
    }
    r = client.put(f"/apartments/{apt_id}", json=update_payload)
    assert r.status_code == 200
    assert round(r.json()["geolocation"]["lat"], 2) == 52.2300

    # Cleanup
    client.delete(f"/apartments/{apt_id}")


def test_duplicate_check_validation(client):
    """Test walidacji dla duplicate check endpoint"""
    # Test bez center i radius, bez bounding_box
    body = {
        "price_min": 1000,
        "price_max": 2000,
    }
    r = client.post("/apartments/duplicates/check", json=body)
    assert r.status_code == 400
    assert "center" in r.json()["detail"].lower() or "bounding_box" in r.json()["detail"].lower()

    # Test z center ale bez radius
    body = {
        "center": {"lat": 52.2297, "lng": 21.0122},
    }
    r = client.post("/apartments/duplicates/check", json=body)
    assert r.status_code == 400

    # Test z radius ale bez center
    body = {
        "radius_m": 150,
    }
    r = client.post("/apartments/duplicates/check", json=body)
    assert r.status_code == 400

    # Test z nieprawidłowym limit (za duży)
    body = {
        "center": {"lat": 52.2297, "lng": 21.0122},
        "radius_m": 150,
        "limit": 300
    }
    r = client.post("/apartments/duplicates/check", json=body)
    assert r.status_code == 400

    # Test z nieprawidłowym limit (za mały)
    body = {
        "center": {"lat": 52.2297, "lng": 21.0122},
        "radius_m": 150,
        "limit": 0
    }
    r = client.post("/apartments/duplicates/check", json=body)
    assert r.status_code == 400


def test_photo_without_style(client):
    """Test photo bez style (None)"""
    # Utwórz apartment
    apt_payload = {
        "source_website": "otodom",
        "source_id": "PH2",
        "source_url": "http://example.com/ph2",
    }
    r = client.post("/apartments", json=apt_payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    # Utwórz photo bez style
    photo_payload = {
        "apartment_id": apt_id,
        "link": "https://example.com/photo_no_style.jpg",
    }
    r = client.post("/photos", json=photo_payload)
    assert r.status_code == 201
    photo_id = r.json()["id"]
    
    # Sprawdź czy style jest None lub nie ma go w odpowiedzi
    assert r.json().get("style") is None or r.json()["style"] is None

    # UPDATE - usuń style (ustaw na pusty string)
    update_payload = {"style": ""}
    r = client.put(f"/photos/{photo_id}", json=update_payload)
    assert r.status_code == 200
    assert r.json().get("style") is None

    # Cleanup
    client.delete(f"/photos/{photo_id}")
    client.delete(f"/apartments/{apt_id}")


def test_apartment_list_pagination(client):
    """Test paginacji w list_apartments"""
    # Utwórz kilka mieszkań
    apt_ids = []
    for i in range(5):
        payload = {
            "source_website": "otodom",
            "source_id": f"PAG{i}",
            "source_url": f"http://example.com/pag{i}",
        }
        r = client.post("/apartments", json=payload)
        assert r.status_code == 201
        apt_ids.append(r.json()["id"])

    # Test z limit
    r = client.get("/apartments?limit=3")
    assert r.status_code == 200
    assert len(r.json()) <= 3

    # Test z skip
    r = client.get("/apartments?skip=2&limit=2")
    assert r.status_code == 200
    results = r.json()
    assert len(results) <= 2

    # Cleanup
    for apt_id in apt_ids:
        client.delete(f"/apartments/{apt_id}")


def test_poi_list_pagination(client):
    """Test paginacji w list_pois"""
    # Utwórz kilka POIs
    poi_ids = []
    for i in range(5):
        payload = {
            "category": "supermarket",
            "geolocation": {"lat": 52.2297 + i * 0.001, "lng": 21.0122 + i * 0.001}
        }
        r = client.post("/pois", json=payload)
        assert r.status_code == 201
        poi_ids.append(r.json()["id"])

    # Test z limit
    r = client.get("/pois?limit=3")
    assert r.status_code == 200
    assert len(r.json()) <= 3

    # Test z skip
    r = client.get("/pois?skip=2&limit=2")
    assert r.status_code == 200
    assert len(r.json()) <= 2

    # Cleanup
    for poi_id in poi_ids:
        client.delete(f"/pois/{poi_id}")
