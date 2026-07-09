"""Charger tests."""

from ev_battery_monitor.domain.charger import Charger


def test_charger_max_power():
    assert Charger(135.0).max_power_kw == 135.0
