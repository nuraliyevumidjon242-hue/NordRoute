from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Callable

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

AUTH_MODE = os.getenv("AUTH_MODE", "api_key").lower()
API_KEY = os.getenv("APP_API_KEY", "local-demo-key-change-me")
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:8080/realms/nordroute").rstrip("/")
OIDC_JWKS_URL = os.getenv(
    "OIDC_JWKS_URL",
    f"{OIDC_ISSUER}/protocol/openid-connect/certs",
)
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "nordroute-dashboard")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "nordroute-dashboard")

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]


@lru_cache(maxsize=1)
def jwks_client() -> PyJWKClient:
    return PyJWKClient(OIDC_JWKS_URL, cache_keys=True, lifespan=300)


def decode_access_token(token: str) -> Principal:
    try:
        signing_key = jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            leeway=30,
        )
    except (jwt.PyJWTError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail={"title": "Invalid or expired access token."},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    realm_roles = claims.get("realm_access", {}).get("roles", [])
    client_roles = claims.get("resource_access", {}).get(OIDC_CLIENT_ID, {}).get("roles", [])
    return Principal(str(claims["sub"]), frozenset(str(role) for role in (*realm_roles, *client_roles)))


async def authenticate(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> Principal:
    if AUTH_MODE == "oidc":
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail={"title": "Sign in with the configured OIDC provider."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        return decode_access_token(credentials.credentials)

    if AUTH_MODE != "api_key":
        raise HTTPException(status_code=503, detail={"title": "Unsupported AUTH_MODE."})

    if API_KEY and x_api_key == API_KEY:
        return Principal("local-demo-dispatcher", frozenset({"admin", "dispatcher", "viewer", "dpo"}))
    raise HTTPException(
        status_code=401,
        detail={"title": "Invalid API key."},
        headers={"WWW-Authenticate": "ApiKey"},
    )


def require_roles(*roles: str) -> Callable:
    async def dependency(
        principal: Annotated[Principal, Depends(authenticate)],
    ) -> Principal:
        if not principal.roles.intersection(roles):
            raise HTTPException(status_code=403, detail={"title": "Insufficient role for this operation."})
        return principal

    return dependency


async def websocket_principal(token: str | None, api_key: str | None) -> Principal:
    if AUTH_MODE == "oidc":
        if not token:
            raise HTTPException(status_code=401, detail={"title": "An access token is required."})
        principal = decode_access_token(token)
        if not principal.roles.intersection({"admin", "dispatcher", "viewer", "dpo"}):
            raise HTTPException(status_code=403, detail={"title": "Insufficient role for the live stream."})
        return principal
    if AUTH_MODE == "api_key" and API_KEY and api_key == API_KEY:
        return Principal("local-demo-dispatcher", frozenset({"admin"}))
    raise HTTPException(status_code=401, detail={"title": "Authentication required."})
