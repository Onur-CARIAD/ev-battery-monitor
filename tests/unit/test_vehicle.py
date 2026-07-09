"""Vehicle tests."""

from ev_battery_monitor.domain.vehicle import Vehicle


def test_vehicle_max_power():
    assert Vehicle(150.0).max_charging_power_kw == 150.0
