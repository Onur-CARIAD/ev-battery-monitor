"""Unit tests for the interactive simulation console (stop-input handling)."""

import threading

from ev_battery_monitor.cli.cli import CLI, _SimulationConsole
from ev_battery_monitor.metrics.metrics import Metrics


def _feed(console: _SimulationConsole, text: str) -> None:
    for char in text:
        console._handle_char(char)


def _console() -> tuple[_SimulationConsole, threading.Event]:
    stop_event = threading.Event()
    console = _SimulationConsole(stop_event)
    console._started = True
    return console, stop_event


def test_typing_stop_sets_stop_event():
    console, stop_event = _console()
    _feed(console, "stop\n")
    assert stop_event.is_set()


def test_typing_stop_char_by_char_ignores_interleaved_output(capsys):
    console, stop_event = _console()
    console._handle_char("s")
    console.print_line("[SoC 30%] tick output")
    console._handle_char("t")
    console.print_line("[SoC 31%] tick output")
    _feed(console, "op\n")
    assert stop_event.is_set()
    out = capsys.readouterr().out
    assert "[SoC 30%] tick output" in out
    assert "[SoC 31%] tick output" in out


def test_unknown_command_locks_and_keeps_running(capsys):
    console, stop_event = _console()
    _feed(console, "help\n")
    assert not stop_event.is_set()
    assert "locked" in capsys.readouterr().out.lower()


def test_empty_line_is_ignored(capsys):
    console, stop_event = _console()
    _feed(console, "\n")
    assert not stop_event.is_set()
    assert "locked" not in capsys.readouterr().out.lower()


def test_whitespace_only_line_is_ignored(capsys):
    console, stop_event = _console()
    _feed(console, "   \n")
    assert not stop_event.is_set()
    assert "locked" not in capsys.readouterr().out.lower()


def test_carriage_return_also_submits():
    console, stop_event = _console()
    _feed(console, "stop\r")
    assert stop_event.is_set()


def test_backspace_edits_buffer_before_submit():
    console, stop_event = _console()
    _feed(console, "ston")
    console._handle_char("\b")  # remove the 'n'
    _feed(console, "p\n")  # now buffer is 'stop'
    assert stop_event.is_set()


def test_backspace_on_empty_buffer_is_safe():
    console, _ = _console()
    console._handle_char("\b")
    assert console._buffer == ""


def test_ctrl_c_behaves_like_stop():
    console, stop_event = _console()
    console._handle_char("\x03")
    assert stop_event.is_set()


def test_non_printable_and_escape_keys_are_ignored():
    console, stop_event = _console()
    console._handle_char("\x00")
    console._handle_char("\x1b")
    console._handle_char("\t")
    assert console._buffer == ""
    assert not stop_event.is_set()


def test_print_line_keeps_prompt_visible(capsys):
    console, _ = _console()
    console.print_line("streamed line")
    out = capsys.readouterr().out
    assert "streamed line" in out
    assert "> " in out


def test_close_without_start_is_safe():
    stop_event = threading.Event()
    console = _SimulationConsole(stop_event)
    console.close()
    assert stop_event.is_set()


def test_start_simulation_completes(config, monkeypatch, capsys):
    monkeypatch.setattr(_SimulationConsole, "start", lambda self: None)
    config._current["runtime.tick_seconds"] = 0.001
    config._current["runtime.speed_factor"] = 1_000_000.0
    config._current["battery.start_soc_percent"] = 79.0
    cli = CLI(config, Metrics())
    cli.start_simulation()
    out = capsys.readouterr().out
    assert "Simulation started" in out
    assert "Simulation completed successfully." in out


def test_start_simulation_stopped_by_user(config, monkeypatch, capsys):
    monkeypatch.setattr(_SimulationConsole, "start", lambda self: self._stop_event.set())
    config._current["runtime.tick_seconds"] = 0.001
    cli = CLI(config, Metrics())
    cli.start_simulation()
    out = capsys.readouterr().out
    assert "Simulation stopped by user." in out
