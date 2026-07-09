"""Charging session parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChargingSession:
    """Target and thermal policy for a charging session."""

    target_soc_percent: float
    cooling_threshold_celsius: float
    cooling_power_reduction_factor: float
