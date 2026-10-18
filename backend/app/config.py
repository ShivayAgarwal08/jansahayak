"""
Configuration alias module redirecting to app.core.config for convenience and compatibility.
"""
from app.core.config import settings, Settings

__all__ = ["settings", "Settings"]
