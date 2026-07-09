# EV Battery Monitor

A Python 3.12 command-line EV battery charging simulation based on the Release 1 technical specification.

## Features

- Interactive CLI: `help`, `show config`, `set`, `reset config`, `start`, `stop`, `metrics`, `exit`
- YAML-based defaults with runtime read-only parameters
- Domain model for battery, vehicle, charger, and charging sessions
- Tick-based simulation engine with cooling hysteresis
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

## Project structure

See `docs/technical-spec.md` for the full implementation contract.
