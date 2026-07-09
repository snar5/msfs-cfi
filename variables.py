"""
Variable definitions for the instrument-trainer SimConnect server.

Each entry maps an internal key to the exact SimConnect variable name,
units, and polling group. The server uses this list to build requests
via python-SimConnect (AircraftRequests) and to label the debug console
output. Keep this file as the single source of truth for "what do we
read from the sim" — the server and debug table should both import it
rather than hardcoding variable names.

Reference: https://docs.flightsimulator.com/html/Programming_Tools/SimVars/
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimVar:
    key: str                  # internal name used in our JSON payload to the client
    sim_name: str              # exact SimConnect variable name (python-SimConnect format)
    units: str                  # units string passed to AircraftRequests
    group: str                   # "session" | "position" | "radios" | "autopilot"
    poll_once: bool = False       # True = fetch once per flight, not every cycle
    notes: str = ""


VARIABLES = [
    # --- session info (fetched once, or on aircraft change) ---
    SimVar("aircraft_title", "TITLE", "", "session", poll_once=True,
           notes="String value, no units param needed."),

    # --- position / state ---
    SimVar("latitude", "PLANE_LATITUDE", "degrees", "position"),
    SimVar("longitude", "PLANE_LONGITUDE", "degrees", "position"),
    SimVar("altitude_indicated", "INDICATED_ALTITUDE", "feet", "position",
           notes="Altimeter reading, accounts for the Kollsman/baro setting. "
                 "Use this (not PLANE_ALTITUDE, which is true/MSL) for "
                 "comparisons against ATC-assigned altitudes."),
    SimVar("heading_magnetic", "PLANE_HEADING_DEGREES_MAGNETIC", "degrees", "position"),
    SimVar("ground_speed", "GROUND_VELOCITY", "knots", "position"),
    SimVar("vertical_speed", "VERTICAL_SPEED", "feet per minute", "position"),

    # --- radios ---
    SimVar("com1_active", "COM_ACTIVE_FREQUENCY:1", "MHz", "radios",
           notes="Request in MHz directly, not the default Frequency BCD16 "
                 "unit — avoids manual BCD decoding and a known rounding "
                 "issue distinguishing .000 from .005 on 8.33kHz spacing."),
    SimVar("com1_standby", "COM_STANDBY_FREQUENCY:1", "MHz", "radios"),
    SimVar("com2_active", "COM_ACTIVE_FREQUENCY:2", "MHz", "radios"),
    SimVar("com2_standby", "COM_STANDBY_FREQUENCY:2", "MHz", "radios"),
    SimVar("nav1_active", "NAV_ACTIVE_FREQUENCY:1", "MHz", "radios",
           notes="Defaults to MHz already, no BCD quirk here."),
    SimVar("nav1_standby", "NAV_STANDBY_FREQUENCY:1", "MHz", "radios"),
    SimVar("nav2_active", "NAV_ACTIVE_FREQUENCY:2", "MHz", "radios"),
    SimVar("nav2_standby", "NAV_STANDBY_FREQUENCY:2", "MHz", "radios"),

    # --- autopilot ---
    SimVar("ap_altitude_bug", "AUTOPILOT_ALTITUDE_LOCK_VAR", "feet", "autopilot",
           notes="Verify against the in-sim altitude bug in debug mode "
                 "before trusting."),
    SimVar("ap_heading_bug", "AUTOPILOT_HEADING_LOCK_DIR", "degrees", "autopilot",
           notes="Verify against the in-sim heading bug in debug mode "
                 "before trusting."),
]
