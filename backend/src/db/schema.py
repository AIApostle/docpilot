"""Database schema verification and initialization helpers for DocPilot."""

import logging
from client.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


async def verify_database_schema() -> bool:
    """Verifies that required DocPilot tables are accessible in Supabase."""
    try:
        supabase = await get_supabase_client()
        # Verify access to key tables
        await supabase.table("doctors").select("id").limit(1).execute()
        await supabase.table("telegram_connections").select("id").limit(1).execute()
        await supabase.table("chat_sessions").select("id").limit(1).execute()
        await supabase.table("docpilot_chat_messages").select("id").limit(1).execute()
        logger.info("DocPilot database schema verification succeeded.")
        return True
    except Exception as exc:
        logger.warning("DocPilot database schema verification encountered: %s", exc)
        return False
