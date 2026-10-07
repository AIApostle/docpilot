"""Centralized Walrus Memory client for persistent doctor-scoped clinical memory."""

import logging
from typing import Any, List, Optional
from client.config import settings

logger = logging.getLogger(__name__)

_walrus_instance: Optional[Any] = None


def get_doctor_namespace(doctor_id: str) -> str:
    """Derives isolated doctor namespace."""
    clean_id = (doctor_id or "").strip().replace("-", "_")
    return f"doctor_{clean_id}"


class WalrusClient:
    """Encapsulates interaction with the persistent MemWal service."""

    def __init__(self):
        self._client: Optional[Any] = None

    async def initialize(self) -> None:
        """Initializes the live persistent MemWal client."""
        if self._client is not None:
            return

        delegate_key = settings.WALRUS_DELEGATE_KEY.strip()
        account_id = settings.WALRUS_ACCOUNT_ID.strip()

        if not settings.WALRUS_ENABLED:
            raise RuntimeError("Walrus memory is disabled; refusing to use non-persistent memory.")
        if not delegate_key or not account_id:
            raise RuntimeError("Walrus memory requires WALRUS_DELEGATE_KEY and WALRUS_ACCOUNT_ID.")

        try:
            from memwal import MemWal

            self._client = MemWal.create(
                key=delegate_key,
                account_id=account_id,
                server_url=settings.WALRUS_SERVER_URL,
                env=settings.WALRUS_ENV,
            )
        except Exception as exc:
            logger.exception("Failed to initialize live MemWal client.")
            raise RuntimeError("Live Walrus memory initialization failed.") from exc

        logger.info("Connected to live Walrus Memory relayer (%s).", settings.WALRUS_ENV)

    async def remember(self, content: str, doctor_id: str) -> bool:
        """Commits clinical content or memory delta to the physician's memory namespace."""
        if not content.strip():
            return False
        await self.initialize()
        namespace = get_doctor_namespace(doctor_id)
        try:
            await self._client.remember_and_wait(
                content.strip(),
                namespace=namespace,
                timeout_ms=60_000,
            )
            logger.info("Committed clinical memory delta to namespace %s.", namespace)
            return True
        except Exception as exc:
            logger.exception("Failed to commit memory to Walrus namespace %s.", namespace)
            raise RuntimeError("Failed to persist clinical memory to Walrus.") from exc

    async def recall(
        self,
        query: str,
        doctor_id: str,
        limit: int = 5,
        min_relevance: float = 0.2,
    ) -> List[str]:
        """Recalls relevant memories for a doctor given a search query or clinical question."""
        if not query.strip():
            return []
        await self.initialize()
        namespace = get_doctor_namespace(doctor_id)
        try:
            recall_kwargs = {
                "query": query.strip(),
                "namespace": namespace,
                "limit": limit,
            }
            if min_relevance is not None:
                recall_kwargs["max_distance"] = max(0.0, 1.0 - float(min_relevance))
            res = await self._client.recall(**recall_kwargs)
            recalled_texts = []
            if res and hasattr(res, "results"):
                for item in res.results:
                    if hasattr(item, "text") and item.text:
                        recalled_texts.append(item.text)
            logger.info("Recalled %d memories for doctor %s.", len(recalled_texts), doctor_id)
            return recalled_texts
        except Exception as exc:
            logger.exception("Failed to recall memories from Walrus namespace %s.", namespace)
            raise RuntimeError("Failed to recall clinical memory from Walrus.") from exc


async def get_walrus_client() -> WalrusClient:
    """Provides singleton WalrusClient instance."""
    global _walrus_instance
    if _walrus_instance is None:
        _walrus_instance = WalrusClient()
        await _walrus_instance.initialize()
    return _walrus_instance
