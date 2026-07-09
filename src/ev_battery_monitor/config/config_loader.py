"""YAML configuration loading."""

from pathlib import Path

import yaml

from ev_battery_monitor.config.config import Config


class ConfigLoader:
    """Load application configuration from YAML."""

    def __init__(self, path: Path | None = None) -> None:
        """Create a loader for a YAML path."""
        self.path = path or Path("config/defaults.yaml")

    def load(self) -> Config:
        """Read YAML and return an in-memory configuration."""
        with self.path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        return Config(raw)
