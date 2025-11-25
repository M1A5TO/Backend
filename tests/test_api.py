import io
import os


def test_apartment_crud_flow(client):
    # Create
    payload = {
        "source_website": "otodom",
        "source_id": "T1",
        "source_url": "http://example.com/apt",
        "city": "Warsaw",
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 201, r.text
    apt = r.json()
    apt_id = apt["id"]

    # Get
    r = client.get(f"/apartments/{apt_id}")
    assert r.status_code == 200
    assert r.json()["city"] == "Warsaw"

    # List
    r = client.get("/apartments?limit=5")
    assert r.status_code == 200
    assert any(a["id"] == apt_id for a in r.json())

    # Update
    r = client.put(f"/apartments/{apt_id}", json={"city": "Krakow"})
    assert r.status_code == 200
    assert r.json()["city"] == "Krakow"

    # Delete
    r = client.delete(f"/apartments/{apt_id}")
    assert r.status_code == 204


def test_photo_upload_stream_update_delete(client):
    # Create apartment for photo
    payload = {
        "source_website": "otodom",
        "source_id": "T2",
        "source_url": "http://example.com/apt2",
        "city": "Gdansk",
    }
    r = client.post("/apartments", json=payload)
    assert r.status_code == 201
    apt_id = r.json()["id"]

    from PIL import Image
    import io

    img = Image.new("RGB", (100,100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    files = {"file": ("test.png", buf, "image/png")}
    data = {"apartment_id": str(apt_id)}
    r = client.post("/photos", files=files, data=data)
    assert r.status_code == 201, r.text
    photo_id = r.json()["id"]

    # Stream file back
    r = client.get(f"/photos/{photo_id}")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/")

    # Update photo: upload another file
    files = {"file": ("test.png", buf, "image/png")}
    r = client.put(f"/photos/{photo_id}", files=files)
    assert r.status_code == 200

    # Delete photo
    r = client.delete(f"/photos/{photo_id}")
    assert r.status_code == 204

    # Cleanup: delete apartment
    client.delete(f"/apartments/{apt_id}")


def test_duplicate_check_endpoint(client):
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
    assert any(match["id"] == apt_id for match in data["matches"])

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


