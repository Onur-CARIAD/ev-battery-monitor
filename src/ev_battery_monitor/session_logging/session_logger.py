"""Per-run simulation log file writer."""

import logging
from datetime import datetime
from pathlib import Path

from ev_battery_monitor.config.config import Config
from ev_battery_monitor.metrics.metrics import Metrics
from ev_battery_monitor.simulation.state import SimulationState


class SessionLogger:
    """Writes a plaintext log file for a single simulation run."""

    def __init__(self, config: Config) -> None:
        """Create a session logger from application configuration."""
        self.config = config
        self.enabled = bool(config.get("logging.enabled"))
        self.directory = Path(str(config.get("logging.directory")))
        self.log_path: Path | None = None
        self._logger: logging.Logger | None = None
        self._handler: logging.FileHandler | None = None

    def start(self) -> None:
        """Open a new timestamped log file and record the current configuration."""
        if not self.enabled:
            return
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self.log_path = self.directory / f"simulation_{timestamp}.log"
            logger = logging.getLogger(f"ev_battery_monitor.session.{timestamp}")
            logger.setLevel(logging.INFO)
            logger.propagate = False
            handler = logging.FileHandler(self.log_path, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(handler)
            self._logger = logger
            self._handler = handler
            self._log_config()
        except OSError as exc:
            self.log_path = None
            self._logger = None
            self._handler = None
            print(f"Warning: simulation logging disabled ({exc}).")

    def log_tick(self, state: SimulationState) -> None:
        """Record a single simulation step."""
        self._log(
            f"tick={state.tick_count} "
            f"soc={state.soc_percent:.1f}% "
            f"temp={state.temperature_celsius:.1f}C "
            f"power={state.charging_power_kw:.1f}kW "
            f"range={state.range_km:.0f}km "
            f"cooling={'ON' if state.cooling else 'OFF'} "
            f"status={state.status}"
        )

    def log_metrics(self, metrics: Metrics) -> None:
        """Record the final metrics snapshot for the run."""
        self._log("Final metrics:\n" + metrics.render())

    def close(self) -> None:
        """Flush and detach the log file handler."""
        if self._logger is not None and self._handler is not None:
            self._logger.removeHandler(self._handler)
            self._handler.close()
        self._logger = None
        self._handler = None

    def _log_config(self) -> None:
        lines = ["Current configuration values:"]
        for key, default, min_value, max_value, current, unit in self.config.rows():
            lines.append(
                f"  {key} = {current} {unit}".rstrip()
                + f" (default={default}, min={min_value}, max={max_value})"
            )
        self._log("\n".join(lines))

    def _log(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)
