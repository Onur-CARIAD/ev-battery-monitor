"""Vehicle domain object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Vehicle:
    """Vehicle charging capabilities."""

    max_charging_power_kw: float
