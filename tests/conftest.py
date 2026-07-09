"""Test fixtures."""

from pathlib import Path

import pytest

from ev_battery_monitor.config.config_loader import ConfigLoader
from ev_battery_monitor.simulation.engine import SimulationEngine


@pytest.fixture
def config():
    return ConfigLoader(Path("config/defaults.yaml")).load()


@pytest.fixture
def fast_config(config):
    config._current["runtime.tick_seconds"] = 1.0
    config._current["runtime.speed_factor"] = 3600.0
    return config


@pytest.fixture
def engine(fast_config):
    return SimulationEngine.from_config(fast_config)
