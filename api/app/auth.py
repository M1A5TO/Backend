"""
Prosty system autentykacji z loginem i hasłem.
Jeden użytkownik, dane w zmiennych środowiskowych.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Konfiguracja
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "2880"))  # 48h domyślnie

# Dane użytkownika z .env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Weryfikuje hasło."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashuje hasło."""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> bool:
    """Sprawdza czy username i password są poprawne."""
    if username != ADMIN_USERNAME:
        return False
    # Jeśli hasło w .env jest już zahashowane, użyj verify_password
    # W przeciwnym razie porównaj bezpośrednio (dla prostoty)
    stored_password = ADMIN_PASSWORD
    
    # Sprawdź czy hasło jest zahashowane (zaczyna się od $2b$)
    if stored_password.startswith("$2b$"):
        return verify_password(password, stored_password)
    else:
        # Proste porównanie (dla developmentu)
        return password == stored_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tworzy JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Weryfikuje JWT token z nagłówka Authorization."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )




