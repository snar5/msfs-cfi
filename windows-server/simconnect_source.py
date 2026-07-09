"""
Real SimVarSource backed by python-SimConnect. Windows-only at runtime
(SimConnect is a Windows DLL) — the import is deferred into connect() so
this module stays importable (just never connectable) on other platforms,
which keeps the rest of the codebase testable via --mock on any machine.
"""

from datasource import ConnectionLost, ConnectionUnavailable
from variables import SimVar


class SimConnectSource:
    def __init__(self) -> None:
        self._sc = None
        self._aq = None

    def connect(self) -> None:
        try:
            from SimConnect import AircraftRequests, SimConnect
        except ImportError as exc:
            raise ConnectionUnavailable(
                f"SimConnect package not available: {exc}"
            ) from exc

        try:
            self._sc = SimConnect()
            # _time=0: no internal value caching — our own poller controls cadence.
            self._aq = AircraftRequests(self._sc, _time=0)
        except Exception as exc:
            raise ConnectionUnavailable(str(exc)) from exc

    def get(self, var: SimVar) -> object:
        if self._aq is None:
            raise ConnectionLost("not connected")
        try:
            value = self._aq.get(var.sim_name)
        except Exception as exc:
            raise ConnectionLost(str(exc)) from exc
        if value is None:
            raise ConnectionLost(f"{var.sim_name} returned None")
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace").rstrip("\x00")
        return value

    def close(self) -> None:
        if self._sc is not None:
            self._sc.exit()
        self._sc = None
        self._aq = None
