"""Simulation engine tests."""

from ev_battery_monitor.simulation.state import SimulationStatus


def test_effective_power_uses_minimum(engine):
    assert engine.effective_power_kw() == 135.0


def test_soc_increases_over_ticks(engine):
    start = engine.battery.soc_percent
    engine.tick()
    assert engine.battery.soc_percent > start


def test_cooling_activates_above_threshold(engine):
    engine.battery.temperature_celsius = 41.0
    engine.tick()
    assert engine.cooling is True


def test_cooling_deactivates_with_hysteresis(engine):
    engine.cooling = True
    engine.battery.temperature_celsius = 36.0
    engine.tick()
    assert engine.cooling is False


def test_status_transitions_to_completed(engine):
    engine.battery.soc_percent = 80.0
    state = engine.tick()
    assert state.status == SimulationStatus.COMPLETED


def test_remaining_time_calculation(engine):
    assert engine.remaining_time_seconds() > 0
