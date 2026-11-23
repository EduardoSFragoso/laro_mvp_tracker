from __future__ import annotations

from laro.config import load_settings


def test_guild_id_vazio_vira_none(monkeypatch):
    monkeypatch.setenv('GUILD_ID', '')
    settings = load_settings(env_file=None)
    assert settings.guild_id is None


def test_guild_id_definido(monkeypatch):
    monkeypatch.setenv('GUILD_ID', '823271452237234208')
    settings = load_settings(env_file=None)
    assert settings.guild_id == 823271452237234208


def test_guild_id_ausente_vira_none(monkeypatch):
    monkeypatch.delenv('GUILD_ID', raising=False)
    settings = load_settings(env_file=None)
    assert settings.guild_id is None


def test_int_env_vazio_usa_default(monkeypatch):
    monkeypatch.setenv('DEL_MSG_AFTER_SECS', '')
    settings = load_settings(env_file=None)
    assert settings.del_msg_after_secs == 10
