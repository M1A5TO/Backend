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


