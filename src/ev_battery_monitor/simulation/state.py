"""Simulation state model."""

from dataclasses import dataclass
from enum import StrEnum


class SimulationStatus(StrEnum):
    """Possible simulation status values."""

    CHARGING = "CHARGING"
    COOLING = "COOLING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class SimulationState:
    """Current simulation state."""

    soc_percent: float
    temperature_celsius: float
    charging_power_kw: float
    range_km: float
    cooling: bool
    status: SimulationStatus
    tick_count: int = 0
