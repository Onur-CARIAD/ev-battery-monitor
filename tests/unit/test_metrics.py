"""Metrics tests."""

from ev_battery_monitor.metrics.metrics import Metrics
from ev_battery_monitor.simulation.state import SimulationState, SimulationStatus


def test_metrics_record_tick():
    metrics = Metrics()
    state = SimulationState(20.0, 25.0, 135.0, 100.0, False, SimulationStatus.CHARGING)
    metrics.record_tick(state, 1.5)
    assert metrics.snapshot().tick_count_total == 1
    assert "Technical Metrics" in metrics.render()
