"""Simulation engine tests."""

from ev_battery_monitor.simulation.state import SimulationStatus


def test_effective_power_uses_minimum(engine):
    assert engine.effective_power_kw() == 135.0


def test_effective_power_reduced_while_cooling(engine):
    engine.cooling = True
    factor = engine.session.cooling_power_reduction_factor
    assert engine.effective_power_kw() == 135.0 * factor
    assert engine.effective_power_kw() < 135.0


def test_soc_increases_over_ticks(engine):
    start = engine.battery.soc_percent
    engine.tick()
    assert engine.battery.soc_percent > start


def test_cooling_activates_above_threshold(engine):
    engine.battery.temperature_celsius = 41.0
    engine.tick()
    assert engine.cooling is True


def test_status_stays_charging_while_cooling(engine):
    engine.config._current["runtime.speed_factor"] = 1.0
    engine.battery.temperature_celsius = 41.0
    state = engine.tick()
    assert engine.cooling is True
    assert state.cooling is True
    assert state.status == SimulationStatus.CHARGING


def test_cooling_deactivates_with_hysteresis(engine):
    engine.cooling = True
    engine.battery.temperature_celsius = 36.0
    engine.tick()
    assert engine.cooling is False


def test_cooling_reduces_temperature(engine):
    engine.cooling = True
    engine.battery.temperature_celsius = 41.0
    before = engine.battery.temperature_celsius
    engine.tick()
    assert engine.cooling is True
    assert engine.battery.temperature_celsius < before


def test_status_transitions_to_completed(engine):
    engine.battery.soc_percent = 80.0
    state = engine.tick()
    assert state.status == SimulationStatus.COMPLETED


def test_remaining_time_calculation(engine):
    assert engine.remaining_time_seconds() > 0
