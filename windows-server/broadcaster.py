"""
WebSocket fan-out: holds the set of connected clients and broadcasts each
poll cycle's payload to all of them. A single client disconnecting or
erroring never affects delivery to the others, and never touches the
poll loop itself.
"""

import asyncio
import json
import logging

import websockets

logger = logging.getLogger(__name__)


class Broadcaster:
    def __init__(self) -> None:
        self._clients: set = set()

    async def register(self, ws) -> None:
        self._clients.add(ws)
        logger.info("Client connected (%d total).", len(self._clients))

    async def unregister(self, ws) -> None:
        self._clients.discard(ws)
        logger.info("Client disconnected (%d total).", len(self._clients))

    async def handler(self, ws) -> None:
        await self.register(ws)
        try:
            async for _ in ws:
                pass  # this server doesn't expect messages from clients
        finally:
            await self.unregister(ws)

    async def broadcast(self, payload: dict) -> None:
        if not self._clients:
            return
        message = json.dumps(payload)
        await asyncio.gather(
            *(self._send_one(ws, message) for ws in list(self._clients)),
            return_exceptions=True,
        )

    async def _send_one(self, ws, message: str) -> None:
        try:
            await ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            self._clients.discard(ws)

    def serve(self, bind_address: str, port: int):
        return websockets.serve(self.handler, bind_address, port)
