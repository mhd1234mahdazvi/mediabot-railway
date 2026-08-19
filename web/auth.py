import os
import time
import hmac
import hashlib
import base64
import json
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# single-admin login; force real credentials in production (Railway env)
PANEL_USERNAME = os.environ.get("PANEL_USERNAME")
PANEL_PASSWORD = os.environ.get("PANEL_PASSWORD")
JWT_SECRET = os.environ.get("JWT_SECRET")
_TOKEN_TTL = 60 * 60 * 12  # 12 hours

if not (PANEL_USERNAME and PANEL_PASSWORD and JWT_SECRET):
    raise RuntimeError(
        "PANEL_USERNAME, PANEL_PASSWORD and JWT_SECRET must be set "
        "(Railway variables). Refusing to start with insecure defaults."
    )
TOKEN_TTL = 60 * 60 * 12  # 12 hours

bearer = HTTPBearer(auto_error=False)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(payload: dict) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64(json.dumps(payload).encode())
    sig = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64(sig)}"


def _verify(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        expected_sig = _b64(
            hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def create_token(username: str) -> str:
    return _sign({"sub": username, "exp": int(time.time()) + _TOKEN_TTL})


def verify_credentials(username: str, password: str) -> bool:
    return (
        hmac.compare_digest(username, PANEL_USERNAME)
        and hmac.compare_digest(password, PANEL_PASSWORD)
    )


def require_auth(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _verify(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload
