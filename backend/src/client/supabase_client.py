from typing import Optional
from fastapi import HTTPException, status
from supabase import AsyncClient, create_async_client
from .config import settings

_async_supabase_client: Optional[AsyncClient] = None
_admin_supabase_client: Optional[AsyncClient] = None


async def get_supabase_client() -> AsyncClient:
    """Provides a singleton async Supabase client instance.

    Raises:
        HTTPException: If SUPABASE_URL or SUPABASE_KEY are not configured.
    """
    global _async_supabase_client

    if _async_supabase_client is not None:
        return _async_supabase_client

    url = settings.SUPABASE_URL.strip()
    key = (settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY or "").strip()

    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Supabase database service is not configured. "
                "Please configure SUPABASE_URL and SUPABASE_KEY in backend/.env."
            ),
        )

    _async_supabase_client = await create_async_client(
        supabase_url=url,
        supabase_key=key,
    )
    return _async_supabase_client


async def get_supabase_admin_client() -> AsyncClient:
    """Provides a server-only Supabase client authenticated with the service role key."""
    global _admin_supabase_client

    if _admin_supabase_client is not None:
        return _admin_supabase_client

    url = settings.SUPABASE_URL.strip()
    key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase admin auth requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
        )

    _admin_supabase_client = await create_async_client(
        supabase_url=url,
        supabase_key=key,
    )
    return _admin_supabase_client


async def close_supabase_client() -> None:
    """Closes any active Supabase client sessions cleanly."""
    global _async_supabase_client, _admin_supabase_client
    for client in (_async_supabase_client, _admin_supabase_client):
        if client is None:
            continue
        try:
            await client.auth.close()
        except Exception:
            pass
    _async_supabase_client = None
    _admin_supabase_client = None
