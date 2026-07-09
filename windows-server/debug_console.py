"""
Live debug table: raw value next to a human-readable display value, so you
can verify a SimVar is wired up correctly before trusting it downstream.
Never re-queries the source — both columns are derived from the same
already-fetched value that also goes out over the wire.
"""

from typing import Callable

from rich.panel import Panel
from rich.table import Table

from variables import SimVar

DEBUG_FORMATTERS: dict[str, Callable[[object], str]] = {
    "degrees": lambda v: f"{v:.1f}°",
    "feet": lambda v: f"{v:,.0f} ft",
    "feet per minute": lambda v: f"{v:+.0f} fpm",
    "knots": lambda v: f"{v:.0f} kt",
    "MHz": lambda v: f"{v:.3f}",
}


def _format_display(var: SimVar, value: object) -> str:
    formatter = DEBUG_FORMATTERS.get(var.units)
    if formatter is None:
        return str(value)
    return formatter(value)


def render_table(payload: dict, variables: list[SimVar]) -> Table:
    table = Table(title="MSFS-CFI Windows Server — live poll")
    table.add_column("Group")
    table.add_column("Key")
    table.add_column("Sim Var")
    table.add_column("Poll")
    table.add_column("Raw")
    table.add_column("Display")

    for var in variables:
        group_data = payload.get(var.group)
        if not group_data or var.key not in group_data:
            continue
        raw = group_data[var.key]
        table.add_row(
            var.group,
            var.key,
            var.sim_name,
            "once" if var.poll_once else "live",
            repr(raw),
            _format_display(var, raw),
        )

    table.caption = f"sequence={payload.get('sequence')} timestamp={payload.get('timestamp')}"
    return table


def render_waiting(message: str, attempt: int) -> Panel:
    body = (
        f"{message}\n\n"
        "Make sure Microsoft Flight Simulator is running with a flight "
        "loaded, then this will connect automatically.\n"
        f"Retry attempt {attempt} (every 5s)..."
    )
    return Panel(body, title="MSFS-CFI Windows Server", border_style="yellow")
