"""
Polling loop: connects to a SimVarSource, filters variables.VARIABLES by
the enabled config groups, fetches each cycle's values, and hands the
assembled JSON-ready payload to a callback (broadcaster + debug console
both subscribe to the same payload each cycle).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable

from config import AppConfig, GroupsConfig
from datasource import ConnectionLost, ConnectionUnavailable, SimVarSource
from variables import SimVar

logger = logging.getLogger(__name__)

RECONNECT_DELAY_S = 5.0

# variables.py's SimVar.group values -> config.toml's [groups] keys.
# Kept as one explicit mapping here rather than renaming either file.
_GROUP_TO_CONFIG_ATTR = {
    "session": "session_info",
    "position": "position",
    "radios": "radios",
    "autopilot": "autopilot",
}


def enabled_groups(groups_cfg: GroupsConfig) -> set[str]:
    return {
        group
        for group, attr in _GROUP_TO_CONFIG_ATTR.items()
        if getattr(groups_cfg, attr)
    }


PayloadCallback = Callable[[dict], Awaitable[None]]


class Poller:
    def __init__(self, source: SimVarSource, variables: list[SimVar], config: AppConfig):
        self._source = source
        self._config = config
        active = enabled_groups(config.groups)
        self._active_vars = [v for v in variables if v.group in active]
        self._poll_once_vars = [v for v in self._active_vars if v.poll_once]
        self._polled_vars = [v for v in self._active_vars if not v.poll_once]
        self._poll_once_cache: dict[str, dict[str, object]] = {}

    async def run(self, on_payload: PayloadCallback) -> None:
        interval_s = self._config.polling.interval_ms / 1000
        while True:
            try:
                self._source.connect()
            except ConnectionUnavailable as exc:
                logger.warning(
                    "SimConnect not available (%s); is MSFS running? Retrying in %.0fs...",
                    exc, RECONNECT_DELAY_S,
                )
                await asyncio.sleep(RECONNECT_DELAY_S)
                continue

            logger.info("Connected. Starting poll loop at %dms interval.", self._config.polling.interval_ms)
            self._poll_once_cache.clear()
            sequence = 0
            try:
                while True:
                    payload = self._build_payload(sequence)
                    sequence += 1
                    await on_payload(payload)
                    await asyncio.sleep(interval_s)
            except ConnectionLost as exc:
                logger.warning("Connection lost (%s); reconnecting...", exc)
                self._source.close()
                continue

    def _build_payload(self, sequence: int) -> dict:
        payload: dict[str, dict[str, object]] = {}

        for var in self._poll_once_vars:
            group = self._poll_once_cache.setdefault(var.group, {})
            if var.key not in group:
                group[var.key] = self._source.get(var)
            payload.setdefault(var.group, {})[var.key] = group[var.key]

        for var in self._polled_vars:
            payload.setdefault(var.group, {})[var.key] = self._source.get(var)

        payload["sequence"] = sequence
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        return payload
