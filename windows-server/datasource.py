"""
Shared contract for "something that can produce SimVar values".

poller.py, broadcaster.py, and debug_console.py all depend only on this
protocol, never on simconnect_source.py or mock_source.py directly — that's
what lets --mock and real SimConnect share the exact same polling/broadcast/
debug-table code path.
"""

from typing import Protocol

from variables import SimVar


class ConnectionUnavailable(Exception):
    """Raised by connect() when the underlying sim link can't be established."""


class ConnectionLost(Exception):
    """Raised by get() when a previously-working link has dropped."""


class SimVarSource(Protocol):
    def connect(self) -> None:
        """Establish the link. Raises ConnectionUnavailable on failure."""
        ...

    def get(self, var: SimVar) -> object:
        """Fetch one variable's current value. Raises ConnectionLost if the link died."""
        ...

    def close(self) -> None:
        """Release any held resources."""
        ...
