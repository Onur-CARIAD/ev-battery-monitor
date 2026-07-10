"""Battery domain object."""

from dataclasses import dataclass


@dataclass
class Battery:
    """EV battery state and calculations."""

    capacity_kwh: float
    soc_percent: float
    temperature_celsius: float
    range_per_kwh_km: float

    def add_energy(self, energy_kwh: float) -> None:
        """Increase state of charge by charged energy."""
        delta_percent = (energy_kwh / self.capacity_kwh) * 100.0
        self.soc_percent = min(100.0, self.soc_percent + delta_percent)

    def heat(self, delta_celsius: float) -> None:
        """Increase battery temperature."""
        self.temperature_celsius += delta_celsius

    def cool(self, delta_celsius: float) -> None:
        """Decrease battery temperature by the active cooling amount."""
        self.temperature_celsius -= delta_celsius

    def estimated_range_km(self) -> float:
        """Return estimated available driving range."""
        usable_kwh = self.capacity_kwh * (self.soc_percent / 100.0)
        return usable_kwh * self.range_per_kwh_km
