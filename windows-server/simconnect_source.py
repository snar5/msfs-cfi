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
            sc = SimConnect()
        except Exception as exc:
            raise ConnectionUnavailable(str(exc)) from exc

        # python-SimConnect can return a "successful" SimConnect() with no
        # exception even when MSFS isn't running: SimConnect_Open can fail
        # without raising OSError, in which case the library silently skips
        # setting up self.timerThread/self.ok instead of erroring. Trusting
        # a clean return here would let a broken half-initialized object
        # through — and its own exit() unconditionally does
        # self.timerThread.join(), so closing it later raises a raw
        # AttributeError instead of a clean reconnect. Verify explicitly.
        if not getattr(sc, "ok", False) or not hasattr(sc, "timerThread"):
            raise ConnectionUnavailable(
                "SimConnect did not report a successful connection (is MSFS running?)"
            )

        try:
            # _time=0: no internal value caching — our own poller controls cadence.
            self._aq = AircraftRequests(sc, _time=0)
        except Exception as exc:
            raise ConnectionUnavailable(str(exc)) from exc
        self._sc = sc

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
        # Guard hasattr(self._sc, "timerThread") too: the library's own exit()
        # does self.timerThread.join() with no existence check, so a partially
        # connected object (see connect() above) would otherwise raise the
        # same upstream AttributeError on close instead of a clean reconnect.
        if self._sc is not None and hasattr(self._sc, "timerThread"):
            self._sc.exit()
        self._sc = None
        self._aq = None
