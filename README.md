# EV Battery Monitor

EV Battery Monitor is a Python command-line application that simulates the charging process of an electric vehicle battery. The application models battery state of charge (SoC), battery temperature, charging power, cooling behavior, remaining charging time, and estimated driving range in real time. 
The project provides an interactive CLI that allows users to configure simulation parameters, start and stop charging sessions, inspect metrics, and analyze charging behavior without requiring any external services. The application can be executed locally or inside a Docker container.

## Authors
T9-J | Squad 32 | Mönsheim

## Download

A ready-to-run bundle is published automatically on every push to `main` and is
available on the **[Releases page](https://github.com/Onur-CARIAD/ev-battery-monitor/releases/latest)**.

The `ev-battery-monitor.zip` asset contains everything needed to run the app
without building from source:

- `ev-battery-monitor.tar` – the prebuilt Docker image
- `docker-compose.yml` – Compose configuration (mounts `./logs`)
- `README.md` – short usage instructions

Download it, then load the image and start the app:

```bash
docker load -i ev-battery-monitor.tar
docker compose run --rm ev-battery-monitor
```

The image is also pushed to Docker Hub and can be pulled directly:

```bash
docker pull <docker-username>/ev-battery-monitor:latest
docker run -it <docker-username>/ev-battery-monitor:latest
```

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

Create and activate a virtual environment, then install the project.

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ev-battery-monitor
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ev-battery-monitor
```

**Windows (cmd):**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
ev-battery-monitor
```

> On PowerShell, if activation is blocked, allow it once with
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Or run the module directly without activating the environment:

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

### Run the prebuilt image from a Release

The `Docker` workflow builds the image on every push to `main` and publishes a
ready-to-run bundle to the
**[Releases page](https://github.com/Onur-CARIAD/ev-battery-monitor/releases/latest)**
as `ev-battery-monitor.zip`, containing:

- `ev-battery-monitor.tar` – the Docker image
- `docker-compose.yml` – Compose configuration (mounts `./logs`)
- `README.md` – short usage instructions

Steps:

1. Open the **Releases** page, download `ev-battery-monitor.zip` and unzip it.
2. Load the image and start the app (per-run logs are written to `./logs`):

   ```bash
   docker load -i ev-battery-monitor.tar
   docker compose run --rm ev-battery-monitor
   ```

No source code or build step is required — everything needed ships in the bundle.

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

See `docs/technical-spec.md` and `docs/blueprint.md` for the full implementation contract.
