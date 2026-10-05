"""Root configuration module re-exporting from src.client.config.

In accordance with project architecture guidelines, client-related configurations
are maintained within src/client/config.py and exposed here for global convenience.
"""

from src.client.config import ClientSettings as Settings
from src.client.config import client_settings, settings

__all__ = ["Settings", "client_settings", "settings"]
