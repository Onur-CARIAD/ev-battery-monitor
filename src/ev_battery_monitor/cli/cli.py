"""Interactive command-line interface."""

import logging
import signal
import sys
import threading
from time import monotonic, sleep

from ev_battery_monitor.config.config import Config
from ev_battery_monitor.exceptions import ConfigError, SimulationError
from ev_battery_monitor.metrics.metrics import Metrics
from ev_battery_monitor.session_logging.session_logger import SessionLogger
from ev_battery_monitor.simulation.engine import SimulationEngine
from ev_battery_monitor.simulation.state import SimulationState, SimulationStatus

LOGGER = logging.getLogger(__name__)
WELCOME_BANNER = r"""
 _____ __     __  ____        _   _
| ____|\ \   / / | __ )  __ _| |_| |_ ___ _ __ _   _
|  _|   \ \ / /  |  _ \ / _` | __| __/ _ \ '__| | | |
| |___   \ V /   | |_) | (_| | |_| ||  __/ |  | |_| |
|_____|   \_/    |____/ \__,_|\__|\__\___|_|   \__, |
                                               |___/
              M o n i t o r i n g   S e r v i c e
"""
WELCOME_TEXT = f"""{WELCOME_BANNER}
Welcome to EV Battery Monitoring Service

  start   Start the charging simulation
  stop    Stop the running simulation
  help    Show all available commands
"""
HELP_TEXT = """EV Battery Monitoring Service – Available Commands

  help              Show this help
  show config       Show current configuration
  set <key> <val>   Override a configuration value
                    Example: set battery.start_soc_percent 20
  reset config      Restore default configuration
  start             Start charging simulation
  stop              Stop running simulation
  metrics           Show current metrics
  exit              Exit application"""


class CLI:
    """EV Battery Monitor interactive CLI."""

    def __init__(self, config: Config, metrics: Metrics) -> None:
        """Initialize the CLI."""
        self.config = config
        self.metrics = metrics
        self.stop_event = threading.Event()
        self._running_simulation = False

    def run(self) -> None:
        """Run the interactive command loop."""
        print(WELCOME_TEXT)
        while True:
            command = input("> ").strip()
            if not self.handle_command(command):
                break

    def handle_command(self, command: str) -> bool:
        """Handle a single command. Return False when the application should exit."""
        if command == "help":
            print(HELP_TEXT)
        elif command == "show config":
            print(self.render_config())
        elif command.startswith("set "):
            self._handle_set(command)
        elif command == "reset config":
            self.config.reset()
            print("Configuration reset to defaults.")
        elif command == "start":
            self.start_simulation()
        elif command == "stop":
            self.stop_event.set()
            print("No running simulation.")
        elif command == "metrics":
            print(self.metrics.render())
        elif command == "exit":
            return False
        elif command:
            print(f"Unknown command: {command}")
        return True

    def render_config(self) -> str:
        """Render current configuration as a fixed-width table."""
        lines = [
            "Parameter                                Default   Min     Max     Current   Unit",
            "----------------------------------------------------------------------------------",
        ]
        for key, default, min_value, max_value, current, unit in self.config.rows():
            lines.append(
                f"{key:<40} {str(default):<9} {str(min_value):<7} "
                f"{str(max_value):<7} {str(current):<9} {unit}"
            )
        return "\n".join(lines)

    def start_simulation(self) -> None:
        """Start and run the charging simulation."""
        session_logger = SessionLogger(self.config)
        try:
            self.config.validate_for_start()
            engine = SimulationEngine.from_config(self.config)
            self.stop_event.clear()
            self.metrics.set_running(True)
            self._running_simulation = True
            session_logger.start()
            print("Simulation started. Type 'stop' to abort.")
            self._install_sigint_handler()
            start = monotonic()
            last_output_soc = -1.0
            while not self.stop_event.is_set():
                tick_start = monotonic()
                state = engine.tick()
                duration_ms = (monotonic() - tick_start) * 1000.0
                self.metrics.record_tick(state, duration_ms)
                session_logger.log_tick(state)
                if state.soc_percent - last_output_soc >= self.config.get(
                    "runtime.output_soc_step_percent"
                ) or state.status in {SimulationStatus.COMPLETED, SimulationStatus.ERROR}:
                    print(self.render_tick(state))
                    last_output_soc = state.soc_percent
                if state.status == SimulationStatus.COMPLETED:
                    print("Simulation completed successfully.")
                    break
                sleep(self.config.get("runtime.tick_seconds"))
            else:
                print("Simulation stopped by user.")
            self.metrics.last_duration_seconds = int(monotonic() - start)
        except ConfigError as exc:
            print(str(exc))
        except SimulationError as exc:
            print(self.render_error(engine.last_state, str(exc)))
        finally:
            self.metrics.set_running(False)
            self._running_simulation = False
            session_logger.log_metrics(self.metrics)
            session_logger.close()
            signal.signal(signal.SIGINT, signal.default_int_handler)

    @staticmethod
    def render_tick(state: SimulationState) -> str:
        """Render a single tick output line."""
        cooling = "ON" if state.cooling else "OFF"
        return (
            f"[SoC {state.soc_percent:>3.0f}%] Temp {state.temperature_celsius:>5.1f} °C | "
            f"Power {state.charging_power_kw:>6.1f} kW | Range {state.range_km:>4.0f} km | "
            f"Cooling {cooling:<3} | {state.status}"
        )

    @staticmethod
    def render_error(state: SimulationState, reason: str) -> str:
        """Render a simulation error."""
        return (
            "Simulation aborted unexpectedly.\n"
            f"Reason: {reason}\n\n"
            "Last State:\n"
            f"  SoC:            {state.soc_percent:.1f} %\n"
            f"  Temperature:    {state.temperature_celsius:.1f} °C\n"
            f"  Charging Power: {state.charging_power_kw:.1f} kW\n"
            f"  Range:          {state.range_km:.0f} km\n"
            "  Status:         ERROR\n\n"
            "Type 'metrics' for more details or 'start' to try again."
        )

    def _handle_set(self, command: str) -> None:
        parts = command.split(maxsplit=2)
        if len(parts) != 3:
            print("Usage: set <key> <val>")
            return
        try:
            self.config.set(parts[1], parts[2])
            print(f"Updated {parts[1]} = {parts[2]}")
        except ConfigError as exc:
            print(str(exc))

    def _install_sigint_handler(self) -> None:
        def handler(signum: int, frame: object) -> None:
            del signum, frame
            if self._running_simulation:
                self.stop_event.set()
            else:
                raise KeyboardInterrupt

        signal.signal(signal.SIGINT, handler)


def locked_input(stop_event: threading.Event) -> None:
    """Read stdin while simulation is running and stop on the stop command."""
    while not stop_event.is_set():
        line = sys.stdin.readline().strip()
        if line == "stop":
            stop_event.set()
            return
        if line:
            print("Commands are locked while simulation is running. Type 'stop' to abort.")
