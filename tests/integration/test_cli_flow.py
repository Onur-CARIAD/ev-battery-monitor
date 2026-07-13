"""CLI integration tests."""

from ev_battery_monitor.cli.cli import CLI, HELP_TEXT, WELCOME_TEXT
from ev_battery_monitor.metrics.metrics import Metrics


def test_help_command_output(config, capsys):
    cli = CLI(config, Metrics())
    cli.handle_command("help")
    assert HELP_TEXT in capsys.readouterr().out


def test_show_config_lists_all_parameters(config):
    cli = CLI(config, Metrics())
    output = cli.render_config()
    assert "battery.capacity_kwh" in output


def test_set_and_show_reflects_change(config):
    cli = CLI(config, Metrics())
    cli.handle_command("set battery.start_soc_percent 30")
    assert "30.0" in cli.render_config()


def test_exit_returns_false(config):
    cli = CLI(config, Metrics())
    assert cli.handle_command("exit") is False


def test_show_config_command_prints_table(config, capsys):
    cli = CLI(config, Metrics())
    assert cli.handle_command("show config") is True
    assert "battery.capacity_kwh" in capsys.readouterr().out


def test_reset_config_restores_defaults(config, capsys):
    cli = CLI(config, Metrics())
    cli.handle_command("set battery.start_soc_percent 30")
    assert cli.handle_command("reset config") is True
    out = capsys.readouterr().out
    assert "Configuration reset to defaults." in out
    assert config.get("battery.start_soc_percent") == 20.0


def test_stop_without_running_simulation(config, capsys):
    cli = CLI(config, Metrics())
    assert cli.handle_command("stop") is True
    assert "No running simulation." in capsys.readouterr().out


def test_metrics_command_prints_metrics(config, capsys):
    cli = CLI(config, Metrics())
    assert cli.handle_command("metrics") is True
    assert "Technical Metrics" in capsys.readouterr().out


def test_unknown_command_reports_error(config, capsys):
    cli = CLI(config, Metrics())
    assert cli.handle_command("does-not-exist") is True
    assert "Unknown command: does-not-exist" in capsys.readouterr().out


def test_empty_command_is_ignored(config, capsys):
    cli = CLI(config, Metrics())
    assert cli.handle_command("") is True
    assert capsys.readouterr().out == ""


def test_set_with_wrong_argument_count(config, capsys):
    cli = CLI(config, Metrics())
    cli.handle_command("set battery.start_soc_percent")
    assert "Usage: set <key> <val>" in capsys.readouterr().out


def test_set_with_invalid_key_reports_error(config, capsys):
    cli = CLI(config, Metrics())
    cli.handle_command("set does.not.exist 5")
    assert "Unknown configuration key" in capsys.readouterr().out


def test_start_command_dispatches_to_simulation(config, monkeypatch):
    cli = CLI(config, Metrics())
    called = []
    monkeypatch.setattr(cli, "start_simulation", lambda: called.append(True))
    assert cli.handle_command("start") is True
    assert called == [True]


def test_run_loop_processes_commands_and_exits(config, capsys, monkeypatch):
    commands = iter(["help", "exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(commands))
    cli = CLI(config, Metrics())
    cli.run()
    out = capsys.readouterr().out
    assert WELCOME_TEXT in out
    assert HELP_TEXT in out
