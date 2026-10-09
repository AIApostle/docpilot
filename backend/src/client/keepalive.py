"""Render anti-spin-down background keep-alive ping client."""

import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse
import httpx

from client.config import settings

logger = logging.getLogger(__name__)

_keepalive_task: Optional[asyncio.Task] = None


def get_render_target_url() -> Optional[str]:
    """Resolves the external application URL for keep-alive pings."""
    if settings.RENDER_EXTERNAL_URL and settings.RENDER_EXTERNAL_URL.strip():
        return settings.RENDER_EXTERNAL_URL.strip().rstrip("/")

    # Check if TELEGRAM_WEBHOOK_URL points to a deployed Render service
    webhook_url = settings.TELEGRAM_WEBHOOK_URL.strip()
    if webhook_url and "onrender.com" in webhook_url:
        try:
            parsed = urlparse(webhook_url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass

    return None


async def ping_endpoint(target_url: str) -> bool:
    """Sends a lightweight GET ping to the specified target health endpoint."""
    url = f"{target_url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "DocPilot-KeepAlive/1.0"}) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                logger.info("Render keep-alive ping to '%s' succeeded (status 200).", url)
                return True
            logger.warning("Render keep-alive ping to '%s' returned status %d.", url, resp.status_code)
            return False
    except Exception as exc:
        logger.warning("Render keep-alive ping to '%s' encountered: %s", url, exc)
        return False


async def _keepalive_loop(target_url: str, interval_seconds: int) -> None:
    """Periodic loop pinging the backend before Render's 15-minute idle spin-down."""
    logger.info(
        "Render anti-spin-down keep-alive worker started. Target: %s, Interval: %ds.",
        target_url,
        interval_seconds,
    )
    # Initial brief delay before starting periodic pings so app finishes booting
    await asyncio.sleep(30)
    while True:
        try:
            await ping_endpoint(target_url)
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Render keep-alive worker cancelled.")
            break
        except Exception as exc:
            logger.warning("Unexpected error in keep-alive worker: %s", exc)
            await asyncio.sleep(interval_seconds)


def start_keepalive_service() -> Optional[asyncio.Task]:
    """Starts the background keep-alive ping loop if configured."""
    global _keepalive_task

    if not settings.RENDER_KEEP_ALIVE_ENABLED:
        logger.info("Render keep-alive service is disabled by configuration.")
        return None

    target_url = get_render_target_url()
    if not target_url:
        logger.info("Render keep-alive service inactive (no external Render URL detected).")
        return None

    if _keepalive_task is not None and not _keepalive_task.done():
        return _keepalive_task

    interval = max(60, int(settings.RENDER_PING_INTERVAL_SECONDS))
    _keepalive_task = asyncio.create_task(
        _keepalive_loop(target_url=target_url, interval_seconds=interval),
        name="docpilot_render_keepalive",
    )
    return _keepalive_task


async def stop_keepalive_service() -> None:
    """Cleanly stops the background keep-alive task on shutdown."""
    global _keepalive_task
    if _keepalive_task and not _keepalive_task.done():
        _keepalive_task.cancel()
        try:
            await _keepalive_task
        except asyncio.CancelledError:
            pass
    _keepalive_task = None
