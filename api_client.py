"""
Klient do obsługi API.
"""
import requests
from typing import Optional, Dict, Any


class AuthClient:
    """Klient do autoryzacji z API."""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        """
        Inicjalizacja klienta autoryzacji.
        
        Args:
            base_url: Bazowy URL API (domyślnie http://localhost:8081)
        """
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.username: Optional[str] = None
    
    def login(self, username: str, password: str) -> bool:
        """
        Loguje użytkownika do API.
        
        Args:
            username: Nazwa użytkownika
            password: Hasło
            
        Returns:
            True jeśli logowanie się powiodło, False w przeciwnym razie
        """
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("access_token")
            self.username = username
            
            if self.token:
                return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"Błąd logowania: {e}")
            if hasattr(e.response, 'text'):
                print(f"Szczegóły: {e.response.text}")
            self.token = None
            self.username = None
            return False
    
    def logout(self):
        """Wylogowuje użytkownika (usuwa token)."""
        self.token = None
        self.username = None
    
    def get_token(self) -> Optional[str]:
        """
        Zwraca aktualny token autoryzacyjny.
        
        Returns:
            Token JWT lub None jeśli użytkownik nie jest zalogowany
        """
        return self.token
    
    def is_authenticated(self) -> bool:
        """
        Sprawdza czy użytkownik jest zalogowany.
        
        Returns:
            True jeśli token istnieje, False w przeciwnym razie
        """
        return self.token is not None
    
    def get_auth_header(self) -> Dict[str, str]:
        """
        Zwraca nagłówek Authorization z tokenem.
        
        Returns:
            Słownik z nagłówkiem Authorization lub pusty słownik jeśli nie jest zalogowany
            
        Raises:
            ValueError: Jeśli użytkownik nie jest zalogowany
        """
        if not self.is_authenticated():
            raise ValueError("Nie jesteś zalogowany. Wywołaj najpierw login().")
        return {"Authorization": f"Bearer {self.token}"}


class APIClient:
    """Klient do komunikacji z API."""
    
    def __init__(self, base_url: str = "http://localhost:8081", auth_client: Optional[AuthClient] = None):
        """
        Inicjalizacja klienta API.
        
        Args:
            base_url: Bazowy URL API (domyślnie http://localhost:8081)
            auth_client: Opcjonalny klient autoryzacji (jeśli None, tworzy nowy)
        """
        self.base_url = base_url.rstrip('/')
        self.auth_client = auth_client or AuthClient(base_url)
    
    def _get_headers(self) -> Dict[str, str]:
        """Zwraca nagłówki z tokenem autoryzacyjnym."""
        headers = {"Content-Type": "application/json"}
        token = self.auth_client.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def get(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Wykonuje żądanie GET do API.
        
        Args:
            path: Ścieżka endpointu (np. "/apartments" lub "/apartments/1")
            
        Returns:
            Odpowiedź JSON jako słownik lub None w przypadku błędu
        """
        if not self.auth_client.is_authenticated():
            raise ValueError("Nie jesteś zalogowany. Wywołaj najpierw login() na auth_client.")
        
        if not path.startswith('/'):
            path = '/' + path
        
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd: {e}")
            raise
    
    def post(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Wykonuje żądanie POST do API.
        
        Args:
            path: Ścieżka endpointu (np. "/apartments")
            payload: Dane do wysłania w body (będą przekonwertowane na JSON)
            
        Returns:
            Odpowiedź JSON jako słownik lub None w przypadku błędu
        """
        if not self.auth_client.is_authenticated():
            raise ValueError("Nie jesteś zalogowany. Wywołaj najpierw login() na auth_client.")
        
        if not path.startswith('/'):
            path = '/' + path
        
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            if response.status_code == 204:
                return None
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd: {e}")
            raise
