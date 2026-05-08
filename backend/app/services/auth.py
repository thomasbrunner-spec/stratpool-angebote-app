"""
Authentication via Supabase JWT.

Frontend logs in via @supabase/ssr → cookies/headers contain JWT.
Backend verifies the JWT with the Supabase JWT secret.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Represents a Supabase-authenticated user."""

    id: str  # Supabase user UUID
    email: str | None = None
    role: str = "authenticated"


def decode_token(token: str) -> dict:
    """Decode and verify a Supabase JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthenticatedUser:
    """FastAPI dependency: extracts and verifies the user from a Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = decode_token(credentials.credentials)

    return AuthenticatedUser(
        id=payload.get("sub", ""),
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
    )


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
