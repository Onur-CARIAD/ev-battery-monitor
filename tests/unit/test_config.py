"""Config tests."""

import pytest

from ev_battery_monitor.exceptions import ConfigKeyError, ConfigValidationError, ConfigValueError


def test_set_valid_value_within_range(config):
    config.set("battery.start_soc_percent", "20.5")
    assert config.get("battery.start_soc_percent") == 20.5


def test_set_value_below_min_raises(config):
    with pytest.raises(ConfigValueError):
        config.set("battery.start_soc_percent", "-1")


def test_set_unknown_key_raises(config):
    with pytest.raises(ConfigKeyError):
        config.set("unknown.key", "1")


def test_bool_parsing_case_insensitive(config):
    config._parameters["demo.flag"] = config._parameters["battery.capacity_kwh"].__class__(
        True, False, True, "", "demo"
    )
    config._current["demo.flag"] = True
    config.set("demo.flag", "False")
    assert config.get("demo.flag") is False


def test_runtime_read_only(config):
    with pytest.raises(ConfigValueError, match="runtime parameters are read-only"):
        config.set("runtime.tick_seconds", "2")


def test_reset_restores_defaults(config):
    config.set("battery.start_soc_percent", "30")
    config.reset()
    assert config.get("battery.start_soc_percent") == 20.0


def test_cross_field_validation(config):
    config.set("battery.start_soc_percent", "90")
    with pytest.raises(ConfigValidationError):
        config.validate_for_start()
