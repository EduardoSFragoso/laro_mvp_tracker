from __future__ import annotations


class BotConfigurationError(RuntimeError):
    """The bot settings are incomplete or invalid (e.g. missing token)."""


class PoolNotInitializedError(RuntimeError):
    """A database operation was attempted before the pool was created."""
