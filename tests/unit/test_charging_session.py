"""Charging session tests."""

from ev_battery_monitor.domain.charging_session import ChargingSession


def test_session_target():
    assert ChargingSession(80.0, 40.0, 0.5).target_soc_percent == 80.0
