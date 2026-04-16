import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings


class SecurityService:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
        return f"{salt}${base64.urlsafe_b64encode(digest).decode()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            salt, digest = password_hash.split("$", maxsplit=1)
        except ValueError:
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
        expected = base64.urlsafe_b64decode(digest.encode())
        return hmac.compare_digest(candidate, expected)

    @staticmethod
    def create_access_token(username: str) -> str:
        expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
        payload = f"{username}:{expires_at}"
        signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        raw = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    @staticmethod
    def decode_token(token: str) -> tuple[str, int]:
        try:
            raw = base64.urlsafe_b64decode(token.encode()).decode()
            username, expires_at, signature = raw.split(":", maxsplit=2)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc

        payload = f"{username}:{expires_at}"
        expected_signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura invalida")

        if int(expires_at) < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")

        return username, int(expires_at)
