"""CLI integration tests."""

from ev_battery_monitor.cli.cli import CLI, HELP_TEXT
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
