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
    """Encapsulates interaction with Walrus Memory (MemWal or MemWalMock)."""

    def __init__(self):
        self._client: Optional[Any] = None
        self._is_mock: bool = False

    async def initialize(self) -> None:
        """Initializes either the live MemWal client or the MemWalMock fallback."""
        if self._client is not None:
            return

        delegate_key = settings.WALRUS_DELEGATE_KEY.strip()
        account_id = settings.WALRUS_ACCOUNT_ID.strip()

        if delegate_key and account_id and settings.WALRUS_ENABLED:
            try:
                from memwal import ENV_PRESETS, MemWal
                env = ENV_PRESETS.get(settings.WALRUS_ENV, ENV_PRESETS["dev"])
                self._client = await MemWal.create(
                    delegate_private_key=delegate_key,
                    account_id=account_id,
                    server_url=settings.WALRUS_SERVER_URL,
                    env=env,
                )
                self._is_mock = False
                logger.info("Connected to live Walrus Memory relayer (%s).", settings.WALRUS_ENV)
                return
            except Exception as exc:
                logger.warning("Failed to initialize live MemWal client (%s). Falling back to MemWalMock.", exc)

        from memwal import MemWalMock
        self._client = MemWalMock()
        self._is_mock = True
        logger.info("Initialized in-memory MemWalMock for clinical memory.")

    async def remember(self, content: str, doctor_id: str) -> bool:
        """Commits clinical content or memory delta to the physician's memory namespace."""
        if not content.strip():
            return False
        await self.initialize()
        namespace = get_doctor_namespace(doctor_id)
        try:
            await self._client.remember(content.strip(), namespace=namespace)
            logger.info("Committed clinical memory delta to namespace %s.", namespace)
            return True
        except Exception as exc:
            logger.error("Failed to commit memory to Walrus (%s): %s", namespace, exc)
            return False

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
            res = await self._client.recall(
                query.strip(),
                namespace=namespace,
                limit=limit,
            )
            recalled_texts = []
            if res and hasattr(res, "results"):
                for item in res.results:
                    if hasattr(item, "text") and item.text:
                        recalled_texts.append(item.text)
            logger.info("Recalled %d memories for doctor %s.", len(recalled_texts), doctor_id)
            return recalled_texts
        except Exception as exc:
            logger.error("Failed to recall memories from Walrus (%s): %s", namespace, exc)
            return []


async def get_walrus_client() -> WalrusClient:
    """Provides singleton WalrusClient instance."""
    global _walrus_instance
    if _walrus_instance is None:
        _walrus_instance = WalrusClient()
        await _walrus_instance.initialize()
    return _walrus_instance
