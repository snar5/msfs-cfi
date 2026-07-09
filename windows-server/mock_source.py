"""
Fake-but-plausible SimVarSource, for exercising the config/poll/broadcast/
debug-table pipeline without a real SimConnect connection (i.e. on a Mac
dev machine, or any machine without MSFS running).

Each polled variable does a small random walk from a plausible baseline
rather than pure noise, so a run looks like a real flight in progress.
"""

import random

from datasource import ConnectionLost
from variables import SimVar

# key -> (baseline, max per-tick drift)
_MOCK_BASELINES: dict[str, tuple[float, float]] = {
    "latitude": (47.450228, 0.00005),
    "longitude": (-122.308792, 0.00005),
    "altitude_indicated": (3500.0, 15.0),
    "heading_magnetic": (270.0, 0.5),
    "ground_speed": (120.0, 2.0),
    "vertical_speed": (-50.0, 10.0),
    "com1_active": (118.3, 0.0),
    "com1_standby": (121.5, 0.0),
    "com2_active": (124.0, 0.0),
    "com2_standby": (122.8, 0.0),
    "nav1_active": (110.3, 0.0),
    "nav1_standby": (108.0, 0.0),
    "nav2_active": (113.0, 0.0),
    "nav2_standby": (111.4, 0.0),
    "ap_altitude_bug": (5000.0, 0.0),
    "ap_heading_bug": (280.0, 0.0),
}

_MOCK_AIRCRAFT_TITLE = "Cessna Skyhawk G1000 Asobo (mock)"


class MockSource:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._state: dict[str, float] = {}

    def connect(self) -> None:
        pass

    def get(self, var: SimVar) -> object:
        if var.key == "aircraft_title":
            return _MOCK_AIRCRAFT_TITLE
        if var.key not in _MOCK_BASELINES:
            raise ConnectionLost(f"no mock baseline defined for {var.key!r}")
        return self._walk(var.key)

    def close(self) -> None:
        pass

    def _walk(self, key: str) -> float:
        baseline, step = _MOCK_BASELINES[key]
        current = self._state.setdefault(key, baseline)
        if step:
            current += self._rng.uniform(-step, step)
            self._state[key] = current
        return current
