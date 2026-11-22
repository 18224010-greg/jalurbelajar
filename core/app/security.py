import hashlib
import hmac
import os
import time
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRE_MINUTES", "10080")) * 60  # 7 hari

# Skema ini hanya agar dokumentasi /docs menampilkan tombol "Authorize".
# Pemeriksaan X-API-Key sebenarnya dilakukan gateway (Nginx).
_api_key_doc = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1, dklen=32
        )
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: int) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + JWT_EXPIRE_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@dataclass
class Principal:
    kind: str  # "apikey" (kelompok lain, server ke server) atau "user" (pengguna aplikasi)
    user_id: int | None = None


def get_principal(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Depends(_bearer),
    _doc_key: str | None = Depends(_api_key_doc),
) -> Principal:
    # Header ini diisi gateway sendiri dan selalu menimpa kiriman klien.
    if request.headers.get("x-gateway-auth") == "key":
        return Principal(kind="apikey")
    if bearer is not None:
        try:
            data = jwt.decode(bearer.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return Principal(kind="user", user_id=int(data["sub"]))
        except (jwt.PyJWTError, KeyError, ValueError):
            pass
    raise HTTPException(
        401,
        "Autentikasi diperlukan: X-API-Key yang valid atau token Bearer yang valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
