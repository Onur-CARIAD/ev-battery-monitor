"""Charger domain object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Charger:
    """External charger capabilities."""

    max_power_kw: float
