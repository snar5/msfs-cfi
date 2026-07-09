"""
Typed loading of config.toml. Deliberately fails fast with a clear message
on a missing/malformed file or missing keys — a bad config is a static setup
error, not a transient condition worth retrying.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class ServerConfig:
    bind_address: str
    port: int


@dataclass(frozen=True)
class PollingConfig:
    interval_ms: int


@dataclass(frozen=True)
class GroupsConfig:
    session_info: bool
    position: bool
    radios: bool
    autopilot: bool


@dataclass(frozen=True)
class DebugConfig:
    enabled: bool


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig
    polling: PollingConfig
    groups: GroupsConfig
    debug: DebugConfig


def load_config(path: Path) -> AppConfig:
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"malformed TOML in {path}: {exc}") from exc

    try:
        return AppConfig(
            server=ServerConfig(**data["server"]),
            polling=PollingConfig(**data["polling"]),
            groups=GroupsConfig(**data["groups"]),
            debug=DebugConfig(**data["debug"]),
        )
    except KeyError as exc:
        raise ConfigError(f"missing required section/key in {path}: {exc}") from exc
    except TypeError as exc:
        raise ConfigError(f"unexpected/missing key in {path}: {exc}") from exc
