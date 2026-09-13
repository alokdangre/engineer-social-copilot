from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from social_manager.config import Settings, get_settings


class AuthenticationError(ValueError):
    pass


class TokenCipher:
    def __init__(self, settings: Settings | None = None) -> None:
        secret = (settings or get_settings()).app_secret_key.get_secret_value().encode()
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
        self._fernet = Fernet(derived_key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise AuthenticationError("Stored connector credential cannot be decrypted") from exc


_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(user_id: str, settings: Settings | None = None) -> str:
    current_settings = settings or get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=current_settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(
        payload,
        current_settings.app_secret_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_access_token(token: str, settings: Settings | None = None) -> str:
    current_settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            current_settings.app_secret_key.get_secret_value(),
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired access token") from exc
    if payload.get("type") != "access" or not isinstance(payload.get("sub"), str):
        raise AuthenticationError("Invalid access token")
    return str(payload["sub"])


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def digest_oauth_state(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode()
    return verifier, challenge.rstrip("=")
