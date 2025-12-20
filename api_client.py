"""
Klient do obsługi API.
"""
import requests
from typing import Optional, Dict, Any

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
