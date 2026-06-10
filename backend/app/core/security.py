from dataclasses import dataclass
from typing import Optional
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

bearer_scheme = HTTPBearer()
_jwks_cache: Optional[dict] = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(settings.keycloak_jwks_uri)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


@dataclass
class CurrentUser:
    sub: str
    full_name: str
    employee_id: Optional[int]
    roles: list[str]

    @property
    def is_installer(self) -> bool:
        return "installer" in self.roles

    @property
    def is_engineer(self) -> bool:
        return "engineer" in self.roles


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )

    roles: list[str] = payload.get("realm_access", {}).get("roles", [])
    return CurrentUser(
        sub=payload["sub"],
        full_name=payload.get("name", ""),
        employee_id=payload.get("employee_id"),
        roles=roles,
    )


def require_installer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_installer:
        raise HTTPException(status_code=403, detail="Installer role required")
    return user


def require_engineer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_engineer:
        raise HTTPException(status_code=403, detail="Engineer role required")
    return user
