# EV Battery Monitor – Container Image

This package contains a ready-to-run Docker image of the EV Battery Monitor and a
Docker Compose file. No source code or build step is required.

## Contents

- `ev-battery-monitor.tar` – the Docker image
- `docker-compose.yml` – Compose configuration (mounts `./logs` for log output)
- `README.md` – this file

## Prerequisites

- Docker with Docker Compose v2 (`docker compose ...`)

## Usage

1. Load the image into Docker:

   ```bash
   docker load -i ev-battery-monitor.tar
   ```

2. Start the application:

   ```bash
   docker compose run --rm ev-battery-monitor
   ```

Type `help` inside the CLI for the available commands.

## Logs

Each simulation run writes a plaintext log file to the `logs/` directory next to
this file (`logs/simulation_<timestamp>.log`). It contains the configuration used,
every simulation tick, and the final metrics.

## Without Compose

You can also run the image directly. Mount a folder to keep the logs on your host:

```bash
docker load -i ev-battery-monitor.tar
docker run -it -v ${PWD}/logs:/app/logs ev-battery-monitor:latest
```
