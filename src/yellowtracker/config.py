from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_TIMEZONE = 'America/Sao_Paulo'


@dataclass(frozen=True)
class Settings:
    """Bot configuration loaded from environment variables (or a .env file)."""

    bot_user_token: str | None
    database_url: str | None
    del_msg_after_secs: int = 10
    table_entry_expiration_mins: int = 20
    timer_delay_secs: int = 5
    timezone: str = DEFAULT_TIMEZONE
    command_prefix: str = '!'
    guild_id: int | None = None


def load_settings(env_file: str | None = '.env') -> Settings:
    if env_file is not None:
        load_dotenv(env_file)

    def int_env(name: str, default: int) -> int:
        raw = os.getenv(name, default=None)
        return int(raw) if raw is not None else default

    guild_id_raw = os.getenv('GUILD_ID', default=None)
    return Settings(
        bot_user_token=os.getenv('BOT_USER_TOKEN'),
        database_url=os.getenv('DATABASE_URL'),
        del_msg_after_secs=int_env('DEL_MSG_AFTER_SECS', 10),
        table_entry_expiration_mins=int_env('TABLE_ENTRY_EXPIRATION_MINS', 20),
        timer_delay_secs=int_env('TIMER_DELAY_SECS', 5),
        timezone=os.getenv('TIMEZONE', default=DEFAULT_TIMEZONE),
        command_prefix=os.getenv('COMMAND_PREFIX', default='!'),
        guild_id=int(guild_id_raw) if guild_id_raw is not None else None,
    )
