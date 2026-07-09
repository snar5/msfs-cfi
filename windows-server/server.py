"""
CLI entrypoint for the MSFS-CFI Windows server.

Usage:
    python server.py --config config.toml            # real SimConnect (Windows only)
    python server.py --mock --config config.toml      # fake data, runs anywhere
"""

import argparse
import asyncio
import logging
from pathlib import Path

from broadcaster import Broadcaster
from config import ConfigError, load_config
from debug_console import render_table, render_waiting
from mock_source import MockSource
from poller import Poller
from simconnect_source import SimConnectSource
from variables import VARIABLES

try:
    from rich.live import Live
except ImportError:
    Live = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MSFS-CFI Windows SimConnect server")
    parser.add_argument(
        "--config", type=Path, default=Path(__file__).parent / "config.toml",
        help="Path to config.toml (default: config.toml next to this script)",
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Use fake generated data instead of a real SimConnect connection",
    )
    parser.add_argument(
        "--mock-seed", type=int, default=None,
        help="Seed for --mock's random walk, for reproducible runs",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        raise SystemExit(f"Config error: {exc}")

    source = MockSource(seed=args.mock_seed) if args.mock else SimConnectSource()
    broadcaster = Broadcaster()
    poller = Poller(source, VARIABLES, config)

    live = Live(refresh_per_second=4) if (config.debug.enabled and Live is not None) else None

    async def on_payload(payload: dict) -> None:
        if live is not None:
            live.update(render_table(payload, VARIABLES))
        await broadcaster.broadcast(payload)

    async def on_waiting(message: str, attempt: int) -> None:
        if live is not None:
            live.update(render_waiting(message, attempt))

    mode = "MOCK" if args.mock else "SimConnect"
    logging.info(
        "Starting server (%s mode) on %s:%d", mode, config.server.bind_address, config.server.port,
    )

    async with broadcaster.serve(config.server.bind_address, config.server.port):
        if live is not None:
            with live:
                await poller.run(on_payload, on_waiting=on_waiting)
        else:
            await poller.run(on_payload, on_waiting=on_waiting)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
