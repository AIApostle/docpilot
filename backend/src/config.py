"""Root configuration module re-exporting from client.config.

In accordance with project architecture guidelines, client-related configurations
are maintained within client/config.py and exposed here for global convenience.
"""

from client.config import ClientSettings as Settings
from client.config import client_settings, settings

__all__ = ["Settings", "client_settings", "settings"]
