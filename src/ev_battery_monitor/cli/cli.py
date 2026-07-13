"""Interactive command-line interface."""

import logging
import os
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
        console = _SimulationConsole(self.stop_event)
        try:
            self.config.validate_for_start()
            engine = SimulationEngine.from_config(self.config)
            self.stop_event.clear()
            self.metrics.set_running(True)
            self._running_simulation = True
            session_logger.start()
            print("Simulation started. Type 'stop' to abort.")
            self._install_sigint_handler()
            console.start()
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
                    console.print_line(self.render_tick(state))
                    last_output_soc = state.soc_percent
                if state.status == SimulationStatus.COMPLETED:
                    console.print_line("Simulation completed successfully.")
                    break
                sleep(self.config.get("runtime.tick_seconds"))
            else:
                console.print_line("Simulation stopped by user.")
            self.metrics.last_duration_seconds = int(monotonic() - start)
        except ConfigError as exc:
            print(str(exc))
        except SimulationError as exc:
            console.print_line(self.render_error(engine.last_state, str(exc)))
        finally:
            self.stop_event.set()
            console.close()
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


def _enable_ansi() -> None:
    """Enable ANSI escape sequence processing on Windows consoles."""
    if os.name != "nt":
        return
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


class _SimulationConsole:
    """Keep user input on its own line while tick output streams above it.

    Reads stdin character by character with software echo so that typing a
    command such as ``stop`` during the simulation is never split across the
    streaming tick output. Only ``stop`` aborts the run; any other input is
    reported as locked (Spec 6 threading model / BP 6).
    """

    PROMPT = "> "

    def __init__(self, stop_event: threading.Event) -> None:
        """Initialize the console with the shared stop event."""
        self._stop_event = stop_event
        self._buffer = ""
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._started = False

    def start(self) -> None:
        """Show the input prompt and start reading stdin in a daemon thread."""
        _enable_ansi()
        self._started = True
        with self._lock:
            self._render_input()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def close(self) -> None:
        """Stop reading input and clear the prompt line."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._started:
            with self._lock:
                sys.stdout.write("\r\x1b[2K")
                sys.stdout.flush()
            self._started = False

    def print_line(self, text: str) -> None:
        """Print a full line above the current input line."""
        with self._lock:
            sys.stdout.write("\r\x1b[2K" + text + "\n")
            self._render_input()

    def _render_input(self) -> None:
        sys.stdout.write("\r\x1b[2K" + self.PROMPT + self._buffer)
        sys.stdout.flush()

    def _submit(self) -> None:
        with self._lock:
            line = self._buffer.strip()
            self._buffer = ""
            sys.stdout.write("\r\x1b[2K" + self.PROMPT + line + "\n")
            self._render_input()
        if line == "stop":
            self._stop_event.set()
        elif line:
            self.print_line(
                "Commands are locked while simulation is running. Type 'stop' to abort."
            )

    def _handle_char(self, char: str) -> None:
        if char in ("\r", "\n"):
            self._submit()
        elif char in ("\b", "\x7f"):
            with self._lock:
                self._buffer = self._buffer[:-1]
                self._render_input()
        elif char == "\x03":
            self._stop_event.set()
        elif char.isprintable():
            with self._lock:
                self._buffer += char
                self._render_input()

    def _read_loop(self) -> None:
        if os.name == "nt":
            self._read_loop_windows()
        else:
            self._read_loop_posix()

    def _read_loop_windows(self) -> None:
        import msvcrt

        while not self._stop_event.is_set():
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in ("\x00", "\xe0"):
                    if msvcrt.kbhit():
                        msvcrt.getwch()
                    continue
                self._handle_char(char)
            else:
                sleep(0.02)

    def _read_loop_posix(self) -> None:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while not self._stop_event.is_set():
                ready, _, _ = select.select([sys.stdin], [], [], 0.05)
                if ready:
                    self._handle_char(sys.stdin.read(1))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
