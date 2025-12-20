"""
Minimalistyczny przykład użycia klienta API.
"""
from api_client import APIClient, AuthClient


# 1. Logowanie
auth = AuthClient("http://localhost:8081")
auth.login("admin", "admin")

# 2. Tworzenie klienta API
api = APIClient("http://localhost:8081", auth_client=auth)

# 3. GET - pobieranie mieszkań
apartments = api.get("/apartments")
print(f"Pobrano {len(apartments)} mieszkań")

# 4. GET - pojedyncze mieszkanie
if apartments:
    apartment_id = apartments[0]["id"]
    apartment = api.get(f"/apartments/{apartment_id}")
    print(f"Mieszkanie: {apartment['city']}")

# 5. POST - tworzenie mieszkania
new_apartment = api.post("/apartments", {
    "source_website": "test",
    "source_id": "TEST001",
    "source_url": "https://example.com",
    "city": "Warsaw",
    "price": 2500.0,
    "footage": 45.5,
    "room_num": 2,
    "currency": "PLN"
})
print(f"Utworzono mieszkanie ID: {new_apartment['id']}")
