"""Session logger tests."""

from ev_battery_monitor.metrics.metrics import Metrics
from ev_battery_monitor.session_logging.session_logger import SessionLogger
from ev_battery_monitor.simulation.state import SimulationState, SimulationStatus


def test_session_logger_writes_config_ticks_and_metrics(config, tmp_path):
    config._current["logging.directory"] = str(tmp_path)
    logger = SessionLogger(config)
    logger.start()

    state = SimulationState(21.0, 26.0, 135.0, 400.0, False, SimulationStatus.CHARGING, 1)
    logger.log_tick(state)

    metrics = Metrics()
    metrics.record_tick(state, 1.5)
    logger.log_metrics(metrics)
    logger.close()

    assert logger.log_path is not None
    content = logger.log_path.read_text(encoding="utf-8")
    assert "Current configuration values:" in content
    assert "battery.capacity_kwh" in content
    assert "tick=1" in content
    assert "Final metrics:" in content


def test_session_logger_disabled_writes_nothing(config, tmp_path):
    config._current["logging.enabled"] = False
    config._current["logging.directory"] = str(tmp_path)
    logger = SessionLogger(config)
    logger.start()
    logger.log_tick(SimulationState(21.0, 26.0, 135.0, 400.0, False, SimulationStatus.CHARGING, 1))
    logger.close()

    assert logger.log_path is None
    assert list(tmp_path.iterdir()) == []
