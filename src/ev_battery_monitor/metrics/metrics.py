"""Technical metrics tracking."""

from dataclasses import dataclass
from time import monotonic

from ev_battery_monitor.simulation.state import SimulationState, SimulationStatus


@dataclass
class MetricsSnapshot:
    """Metrics output snapshot."""

    uptime_seconds: int
    tick_count_total: int
    tick_duration_ms: float
    simulation_running: bool
    last_state: SimulationState | None
    duration_seconds: int


class Metrics:
    """Collects runtime and simulation metrics."""

    def __init__(self) -> None:
        """Initialize metric counters."""
        self.started_at = monotonic()
        self.tick_count_total = 0
        self.tick_duration_ms = 0.0
        self.simulation_running = False
        self.last_state: SimulationState | None = None
        self.last_duration_seconds = 0

    def record_tick(self, state: SimulationState, duration_ms: float) -> None:
        """Record a completed simulation tick."""
        self.tick_count_total += 1
        self.tick_duration_ms = duration_ms
        self.last_state = state

    def set_running(self, running: bool) -> None:
        """Set whether a simulation is currently running."""
        self.simulation_running = running

    def snapshot(self) -> MetricsSnapshot:
        """Return a current metrics snapshot."""
        return MetricsSnapshot(
            uptime_seconds=int(monotonic() - self.started_at),
            tick_count_total=self.tick_count_total,
            tick_duration_ms=self.tick_duration_ms,
            simulation_running=self.simulation_running,
            last_state=self.last_state,
            duration_seconds=self.last_duration_seconds,
        )

    def render(self) -> str:
        """Render metrics in the specified text format."""
        snapshot = self.snapshot()
        state = snapshot.last_state or SimulationState(0.0, 0.0, 0.0, 0.0, False, SimulationStatus.CHARGING)
        return (
            "Technical Metrics\n"
            "-----------------\n"
            f"uptime_seconds:      {snapshot.uptime_seconds}\n"
            f"tick_count_total:    {snapshot.tick_count_total}\n"
            f"tick_duration_ms:    {snapshot.tick_duration_ms:.2f}\n"
            f"simulation_running:  {str(snapshot.simulation_running).lower()}\n\n"
            "Last Simulation Result\n"
            "----------------------\n"
            f"final_soc_percent:       {state.soc_percent:.1f}\n"
            f"final_temperature:       {state.temperature_celsius:.1f} °C\n"
            f"final_range_km:          {state.range_km:.0f}\n"
            f"final_status:            {state.status}\n"
            f"duration_seconds:        {snapshot.duration_seconds}"
        )
