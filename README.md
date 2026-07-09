# MSFS instrument training instructor

## What this is

A tool that simulates an instrument-training instructor during hood work in
MSFS 2020. Real instrument training happens on clear days under a hood, with
an instructor roleplaying ATC and prompting the student through
departure/enroute/approach/landing tasks. This project automates that role:
it watches the flight via SimConnect, ingests a flight plan, and gives
text-caption reminders and simulated ATC-style calls at the right moments.
It is explicitly **not** a replacement for real ATC or real instruction —
a training aid only.

## Architecture (three tiers)

1. **Windows server** (Python) — the only piece that can touch SimConnect,
   since it's a Windows-only DLL. Polls sim variables and exposes them over
   the LAN as JSON (WebSocket).
2. **Instructor engine** (Python, runs on Mac/Linux) — ingests the flight
   plan, tracks flight phase, runs deviation/frequency/vector checks,
   decides what the "instructor" should say.
3. **Client GUI** (Tauri, native desktop app on Mac/Linux) — displays
   captions/checklists/altitude info. Talks to the engine over local
   WebSocket. The engine stays Python; Tauri is just the shell.

## Confirmed scope decisions

- **Communication style: text captions only.** No TTS, no STT, no two-way
  voice. Simplifies everything — no audio pipeline, no latency concerns.
- **GUI: Tauri.** Run the Python engine as a separate local process for now;
  bundling it as a Tauri sidecar (single-binary packaging via PyInstaller)
  is a later polish step, not a v1 concern.
- **Approach altitude compliance: manual entry for v1.** Schema is a simple
  list of `{fix_name, constraint_type, altitude_ft, note}` per approach.
  Deliberately generic so an "AI-assisted chart parsing" feature could
  populate the same structure later (with human confirmation before trust)
  without a redesign. Not building the automated parsing now.
- **Mileage-based reminders** (e.g. "10nm from destination, check ATIS"):
  default 10nm, configurable per flight and eventually per-waypoint.
  Computed via great-circle distance from live position (server) to
  SimBrief waypoint coordinates (already ingested) — does **not** require
  reading MSFS's internal flight plan state.
- **Vector-to-intercept math: deterministic geometry**, not LLM-computed.
  If an LLM is used at all, it's only for phrasing captions naturally, never
  for computing headings/altitudes/distances.
- **Explicitly deferred / out of scope for v1**: voice interaction, two-way
  AI ATC conversation, automated CIFP/approach-chart parsing, Tauri sidecar
  packaging.

## Data sources

- **Flight plan**: SimBrief public API (pilot ID → OFP JSON). Not extracted
  from MSFS — SimConnect can't reliably expose the full waypoint list (known
  community limitation: only next/prev waypoint + index/count are exposed
  cleanly; full-list workarounds are flaky and MSFS injects synthetic
  waypoints). SimBrief is the source of truth for the planned route.
- **Navdata** (airport/navaid frequencies, runways): X-Plane's free
  `earth_nav.dat` / `earth_awy.dat`, or OurAirports CSV exports. Worldwide,
  free, easy to parse.
- **Weather / simulated ATIS**: live METAR from aviationweather.gov (MSFS
  live weather generally mirrors real-world conditions). Active runway
  computed from wind vs. runway heading.
- **Approach altitude constraints**: manual entry, v1.

## Windows server — status and design

- Console app for now (background/startup service is a later step).
- Config file: `config.toml` — bind address/port, poll interval, per-group
  enable/disable toggles, debug mode flag.
- Debug mode: live console table each polling cycle, raw SimConnect value
  next to converted/display value, to verify correctness before trusting
  data downstream.
- Variable groups (see `variables.py`):
  - **session** (fetch once, not polled): aircraft title (`TITLE`)
  - **position** (polled): lat, lon, indicated altitude, magnetic heading,
    ground speed, vertical speed
  - **radios** (polled): COM1/COM2 active+standby, NAV1/NAV2 active+standby
  - **autopilot** (polled): altitude bug, heading bug

### Known SimConnect quirks (already handled in `variables.py`)

- **COM frequencies** default to `"Frequency BCD16"` units, which is a pain
  to decode and has a rounding bug that can't distinguish `.000` from
  `.005` on 8.33kHz-spaced frequencies. Fix: request them directly in
  `"MHz"` units instead — SimConnect converts for you.
- **Altitude**: use `INDICATED_ALTITUDE` (accounts for the barometric/
  Kollsman setting — what the pilot's altimeter shows and what ATC
  assignments are based on), not `PLANE_ALTITUDE` (true altitude / MSL).
- **Full flight plan waypoint list**: not reliably readable via SimConnect.
  Not needed — see Data sources above.

## Prior related work

An earlier project had a Windows server talking to SimConnect with a
Mac/Linux client — but the server logic was specific to a CRJ700's CDU and
isn't reusable here. The client/server-over-LAN pattern itself is proven,
though; this project rebuilds the server with a generic, aircraft-agnostic
variable set instead.

## Next steps

1. Build the Windows server: SimConnect polling loop, config loading,
   JSON-over-WebSocket output, debug console table.
2. Build the Mac/Linux instructor engine: SimBrief ingestion, phase
   detection, frequency/altitude/vector checks, caption generation.
3. Build the Tauri client: connects to the engine, displays captions and
   checklists.