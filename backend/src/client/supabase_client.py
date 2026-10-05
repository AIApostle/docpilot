from typing import Optional
from fastapi import HTTPException, status
from supabase import AsyncClient, create_async_client
from .config import settings

_async_supabase_client: Optional[AsyncClient] = None


async def get_supabase_client() -> AsyncClient:
    """Provides a singleton async Supabase client instance.

    Raises:
        HTTPException: If SUPABASE_URL or SUPABASE_KEY are not configured.
    """
    global _async_supabase_client

    if _async_supabase_client is not None:
        return _async_supabase_client

    url = settings.SUPABASE_URL.strip()
    key = (settings.SUPABASE_KEY or settings.SUPABASE_ANON_KEY).strip()

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


async def close_supabase_client() -> None:
    """Closes any active Supabase client sessions cleanly."""
    global _async_supabase_client
    if _async_supabase_client is not None:
        try:
            await _async_supabase_client.auth.close()
        except Exception:
            pass
        finally:
            _async_supabase_client = None
