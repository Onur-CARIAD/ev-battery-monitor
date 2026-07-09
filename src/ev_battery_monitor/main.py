"""Application entry point."""

import logging
import os
import sys

from ev_battery_monitor.cli.cli import CLI
from ev_battery_monitor.config.config_loader import ConfigLoader
from ev_battery_monitor.metrics.metrics import Metrics


def configure_logging() -> None:
    """Configure standard-library logging."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    """Start EV Battery Monitoring Service."""
    configure_logging()
    config = ConfigLoader().load()
    metrics = Metrics()
    CLI(config, metrics).run()


if __name__ == "__main__":
    main()
