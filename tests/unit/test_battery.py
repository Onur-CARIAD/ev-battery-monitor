"""Battery tests."""

from ev_battery_monitor.domain.battery import Battery


def test_battery_add_energy_increases_soc():
    battery = Battery(100.0, 10.0, 20.0, 5.0)
    battery.add_energy(10.0)
    assert battery.soc_percent == 20.0


def test_range_calculation():
    battery = Battery(100.0, 50.0, 20.0, 5.0)
    assert battery.estimated_range_km() == 250.0
