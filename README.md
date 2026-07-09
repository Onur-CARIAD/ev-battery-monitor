# EV Battery Monitor

A Python 3.12 command-line EV battery charging simulation based on the Release 1 technical specification.

## Features

- Interactive CLI: `help`, `show config`, `set`, `reset config`, `start`, `stop`, `metrics`, `exit`
- YAML-based defaults with runtime read-only parameters
- Domain model for battery, vehicle, charger, and charging sessions
- Tick-based simulation engine with cooling hysteresis
- Per-run plaintext log files (configuration, every tick, final metrics)
- Technical metrics
- Docker support
- GitHub Actions for linting, formatting, tests, and Docker build

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ev-battery-monitor
```

Or:

```bash
python -m ev_battery_monitor.main
```

## Tests

```bash
ruff check .
black --check .
pytest --cov=ev_battery_monitor --cov-report=xml
```

## Docker

```bash
docker build -t ev-battery-monitor:latest .
docker run -it ev-battery-monitor:latest
```

### Docker Compose

Start the application and persist simulation logs to the host `./logs` folder:

```bash
docker compose run --rm ev-battery-monitor
```

The `docker-compose.yml` builds the image on demand, runs the CLI interactively
and mounts `./logs` into the container so per-run log files stay on the host.

## Logging

Each simulation run writes a plaintext log file to the `logs/` directory
(`logs/simulation_<timestamp>.log`). The file contains:

- the current configuration values at start
- every simulation tick (SoC, temperature, power, range, cooling, status)
- the final metrics snapshot

Logging is configurable in `config/defaults.yaml`:

| Key                 | Default | Description                         |
| ------------------- | ------- | ----------------------------------- |
| `logging.enabled`   | `true`  | Enable or disable per-run log files |
| `logging.directory` | `logs`  | Target directory for log files      |

When running in Docker, mount the log directory to retrieve the files:

```bash
docker run -it -v ${PWD}/logs:/app/logs ev-battery-monitor:latest
```

## Project structure

See `docs/technical-spec.md` for the full implementation contract.
