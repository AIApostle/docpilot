"""Walrus Memory integration facade.

Re-exports client.walrus for consistent domain modeling.
"""

from client.walrus import WalrusClient, get_doctor_namespace, get_walrus_client

__all__ = ["WalrusClient", "get_doctor_namespace", "get_walrus_client"]
