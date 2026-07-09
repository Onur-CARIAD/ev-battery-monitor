# EV Battery Monitoring Service – Technical Specification

**Version:** 1.1
**Status:** Draft
**Companion Document:** `blueprint.md`
**Scope:** Release 1

Dieses Dokument ergänzt den fachlichen Blueprint um die technischen Rahmenbedingungen. Es dient als Vorgabe für die Implementierung (auch mit GitHub Copilot) und stellt sicher, dass keine Annahmen implizit bleiben.

---

## 1. Technische Rahmenbedingungen

### 1.1 Sprache und Version

- **Sprache:** Python
- **Version:** 3.12
- **Type Hints:** verpflichtend, moderner Stil erlaubt (`float | None`)
- **Style Guide:** PEP 8
- **Formatter:** `black`
- **Linter:** `ruff`
- **Docstrings:** Google-Style, für alle öffentlichen Klassen und Methoden

### 1.2 Abhängigkeiten

Alle Dependencies werden **ausschließlich in `pyproject.toml`** deklariert. Es gibt **keine `requirements.txt`**.

| Paket | Zweck | Version | Gruppe |
|-------|-------|---------|--------|
| `PyYAML` | Laden der Default-Config | >= 6.0 | main |
| `pytest` | Unit Tests | >= 8.0 | dev |
| `pytest-cov` | Coverage Reports | >= 5.0 | dev |
| `ruff` | Linting | >= 0.5 | dev |
| `black` | Formatting | >= 24.0 | dev |

Keine Nutzung von:

- FastAPI
- Pydantic
- Rich / Colorama
- asyncio

### 1.3 Package-Konventionen

- **Root-Package:** `ev_battery_monitor`
- **Imports:** absolut (`from ev_battery_monitor.domain.battery import Battery`)
- **Keine relativen Imports.**

### 1.4 `pyproject.toml`-Skizze

```toml
[project]
name = "ev-battery-monitor"
version = "0.1.0"
description = "EV Battery Monitoring Service – Release 1"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Holger Meister" }]

dependencies = [
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "black>=24.0",
]

[project.scripts]
ev-battery-monitor = "ev_battery_monitor.main:main"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"

[tool.coverage.run]
source = ["ev_battery_monitor"]
branch = true

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.black]
line-length = 100
target-version = ["py312"]
```

---

## 2. Projektstruktur

```text
ev-battery-monitor/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── docker.yml
├── docs/
│   ├── blueprint.md
│   └── technical-spec.md
├── config/
│   └── defaults.yaml
├── src/
│   └── ev_battery_monitor/
│       ├── __init__.py
│       ├── main.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── config_loader.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── battery.py
│       │   ├── vehicle.py
│       │   ├── charger.py
│       │   └── charging_session.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   └── state.py
│       ├── metrics/
│       │   ├── __init__.py
│       │   └── metrics.py
│       └── cli/
│           ├── __init__.py
│           └── cli.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_battery.py
│   │   ├── test_vehicle.py
│   │   ├── test_charger.py
│   │   ├── test_charging_session.py
│   │   ├── test_engine.py
│   │   └── test_metrics.py
│   └── integration/
│       └── test_cli_flow.py
├── Dockerfile
├── .dockerignore
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 3. GitHub Actions

Alle Workflows liegen unter `.github/workflows/`. Für Release 1 sind zwei Workflows vorgesehen.

### 3.1 `ci.yml` – Continuous Integration

**Trigger:**

- `push` auf alle Branches
- `pull_request` gegen `main`

**Jobs:**

1. **Lint & Format**
   - `ruff check .`
   - `black --check .`

2. **Tests**
   - Matrix: Python 3.12
   - `pip install -e ".[dev]"`
   - `pytest --cov=ev_battery_monitor --cov-report=xml`

3. **Coverage-Upload (optional)**
   - Artifact-Upload des Coverage-Reports

### 3.2 `docker.yml` – Docker Image Build

**Trigger:**

- `push` auf `main`
- manuelles `workflow_dispatch`

**Jobs:**

1. **Build**
   - Docker Buildx
   - `docker build -t ev-battery-monitor:latest .`

2. **Smoke-Test (optional)**
   - Container starten
   - Prüfen, dass die Startausgabe erscheint (`help`-Kommando pipen)

### 3.3 Konventionen

- Keine Secrets in Release 1
- Kein Push zu einer Registry in Release 1
- Kein Deployment
- Cache für `pip` aktiv (`actions/cache`)

---

## 4. Runtime-Konstanten und Config-Erweiterung

Die folgenden Werte sind Simulations-Runtime-Parameter. Sie **gehören in die YAML** (nicht in den Code), sind aber **nicht per `set` änderbar**. Sie werden nur zum App-Start aus der YAML gelesen.

### 4.1 Erweiterung `defaults.yaml`

```yaml
runtime:
  tick_seconds:
    default: 1.0
    unit: s
    description: Reale Dauer eines Simulationsticks

  speed_factor:
    default: 60.0
    unit: x
    description: Wie viele simulierte Sekunden pro realer Sekunde

  heating_factor:
    default: 0.0008
    unit: "°C/kW/Tick"
    description: Erwärmungsfaktor pro kW Ladeleistung pro Tick

  output_soc_step_percent:
    default: 1.0
    unit: "%"
    description: SoC-Schrittweite, ab der eine neue Ausgabe erfolgt

  cooling_hysteresis_celsius:
    default: 3.0
    unit: "°C"
    description: Hysterese der Kühlungs-Rückschaltung
```

### 4.2 Verhalten

- `runtime`-Sektion ist **read-only** zur Laufzeit
- `set runtime.tick_seconds ...` → Ablehnung mit Meldung: „runtime parameters are read-only"

---

## 5. Config-System

### 5.1 Datenstruktur pro Parameter

```python
{
    "default": <value>,
    "min":     <value> | None,   # None für read-only Runtime-Werte
    "max":     <value> | None,
    "unit":    <str>,
    "description": <str>,
}
```

### 5.2 Input-Parsing für `set`

| Zieltyp | Erlaubte Strings |
|---------|------------------|
| `float` | `"20"`, `"20.5"`, `"1.5e2"` |
| `bool`  | `"true"`, `"false"`, `"True"`, `"False"` (case-insensitive) |

Nicht parsbare Werte → Fehler:

```text
Invalid value 'abc' for battery.start_soc_percent
Expected type: float (0.0 – 100.0)
```

### 5.3 Cross-Field-Validierung

Bei `start`-Kommando geprüft:

1. `battery.start_soc_percent < session.target_soc_percent`
2. `battery.start_temperature_celsius < session.cooling_threshold_celsius + 20`
3. `charger.max_power_kw > 0` und `vehicle.max_charging_power_kw > 0`

Bei Verletzung → `start` wird nicht ausgeführt, Fehlermeldung mit Verweis auf betroffenen Parameter.

### 5.4 Reset-Verhalten

- `reset config` setzt **alle** Parameter auf die YAML-Defaults zurück.
- Die YAML wird dabei **nicht neu gelesen** (der geladene In-Memory-Snapshot ist die Quelle).
- Der YAML-Snapshot wird einmalig beim App-Start eingefroren.

---

## 6. Threading-Modell

### 6.1 Grundprinzip

- **`threading`** aus der Standardbibliothek, kein `asyncio`.
- Zwei Threads während der Simulation:

```text
Main-Thread:
  - führt SimulationEngine.tick() aus
  - prüft stop_event nach jedem Tick

Input-Thread (Daemon):
  - blockiert auf sys.stdin.readline()
  - erkennt Eingaben ("stop" oder andere)
  - setzt stop_event bei "stop"
  - meldet andere Kommandos als "gesperrt"
```

### 6.2 Kommunikation

- `threading.Event` als `stop_event`
- Optional: `queue.Queue` für Nachrichten vom Input-Thread an den CLI

### 6.3 Signalverhalten (SIGINT / Ctrl+C)

- Während Simulation: verhält sich wie `stop`
  → sauberer Abschluss des aktuellen Ticks, Rückkehr ins CLI
- Außerhalb der Simulation: normaler Programmabbruch (Standard-Handler)

Umsetzung über `signal.signal(signal.SIGINT, handler)`.

---

## 7. Logging

### 7.1 Framework

- Standardbibliothek `logging`
- Kein Drittanbieter-Logger

### 7.2 Konfiguration

- Ziel: `stdout`
- Format:

```text
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

- Default Log-Level: `INFO`
- Debug-Level aktivierbar über Umgebungsvariable `LOG_LEVEL=DEBUG`

### 7.3 Verwendung

| Ebene | Beispiel |
|-------|----------|
| DEBUG | Tick-interne Zwischenwerte |
| INFO  | Simulation gestartet, beendet, Config geladen |
| WARN  | Ungültige Nutzereingabe, Cross-Field-Warnungen |
| ERROR | Exception in SimulationEngine |

### 7.4 Nicht loggen

- Konsolenausgaben der Simulation (das ist reine `print`-Ausgabe)
- Nutzereingaben (Privacy / Übersichtlichkeit)

---

## 8. Ausgabeformate (Templates)

### 8.1 Tick-Ausgabe

```text
[SoC {soc:>3.0f}%] Temp {temp:>5.1f} °C | Power {power:>6.1f} kW | Range {range:>4.0f} km | Cooling {cooling:<3} | {status}
```

Wobei:

- `cooling` = `"ON"` oder `"OFF"`
- `status` = `CHARGING` / `COOLING` / `COMPLETED`

Beispiel:

```text
[SoC  22%] Temp  27.6 °C | Power  135.0 kW | Range   96 km | Cooling OFF | CHARGING
```

### 8.2 Simulations-Start-Meldung

```text
Simulation started. Type 'stop' to abort.
```

### 8.3 Simulations-Ende-Meldung

```text
Simulation completed successfully.
```

### 8.4 Stop-Meldung

```text
Simulation stopped by user.
```

### 8.5 Fehlermeldung

```text
Simulation aborted unexpectedly.
Reason: {reason}

Last State:
  SoC:            {soc:.1f} %
  Temperature:    {temp:.1f} °C
  Charging Power: {power:.1f} kW
  Range:          {range:.0f} km
  Status:         ERROR

Type 'metrics' for more details or 'start' to try again.
```

### 8.6 `show config`-Ausgabe

Spaltenformat, fixe Breiten:

```text
Parameter                                Default   Min     Max     Current   Unit
----------------------------------------------------------------------------------
battery.capacity_kwh                     77.0      20.0    200.0   77.0      kWh
...
```

### 8.7 `metrics`-Ausgabe

```text
Technical Metrics
-----------------
uptime_seconds:      {uptime}
tick_count_total:    {ticks}
tick_duration_ms:    {duration:.2f}
simulation_running:  {running}

Last Simulation Result
----------------------
final_soc_percent:       {soc:.1f}
final_temperature:       {temp:.1f} °C
final_range_km:          {range:.0f}
final_status:            {status}
duration_seconds:        {duration_s}
```

### 8.8 `help`-Ausgabe (festgeschrieben)

```text
EV Battery Monitoring Service – Available Commands

  help              Show this help
  show config       Show current configuration
  set <key> <val>   Override a configuration value
                    Example: set battery.start_soc_percent 20
  reset config      Restore default configuration
  start             Start charging simulation
  stop              Stop running simulation
  metrics           Show current metrics
  exit              Exit application
```

---

## 9. Dockerfile-Spezifikation

### 9.1 Vorgaben

- **Base Image:** `python:3.12-slim`
- **Multi-Stage:** nein (Release 1 klein halten)
- **Non-root User:** ja (`app`)
- **Working Directory:** `/app`
- **Kein Volume**
- **Kein Port**
- **Kein HEALTHCHECK** (Release 1)
- **Install via `pyproject.toml`** (kein `requirements.txt`)

### 9.2 Dockerfile-Skizze

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/

RUN pip install --no-cache-dir .

USER app

CMD ["python", "-m", "ev_battery_monitor.main"]
```

### 9.3 `.dockerignore`

```text
__pycache__/
*.pyc
.pytest_cache/
.venv/
.git/
.github/
.gitignore
tests/
docs/
```

---

## 10. Startverhalten

### 10.1 Ablauf beim Container-Start

```text
1. main.py wird ausgeführt
2. Logging wird initialisiert
3. ConfigLoader liest config/defaults.yaml
4. Config-Objekt wird in-memory erzeugt
5. Metrics.start_uptime() wird aufgerufen
6. CLI.run() startet interaktive Schleife
```

### 10.2 Startausgabe

```text
Welcome to EV Battery Monitoring Service
Type 'help' for available commands.

>
```

---

## 11. Fehler- und Ausnahmebehandlung

### 11.1 Prinzipien

- Keine ungefangenen Exceptions dürfen die App beenden.
- Fehler bei Nutzereingaben → freundliche CLI-Meldung, App läuft weiter.
- Fehler in `SimulationEngine.tick()` → geordneter Übergang in Status `ERROR`, Rückkehr ins CLI.

### 11.2 Exception-Hierarchie

```text
EvBatteryMonitorError                (Base)
├── ConfigError
│   ├── ConfigKeyError
│   ├── ConfigValueError
│   └── ConfigValidationError
└── SimulationError
    ├── SimulationStateError
    └── SimulationRuntimeError
```

### 11.3 Verhalten

- `ConfigError` → CLI zeigt Meldung, wartet auf nächstes Kommando
- `SimulationError` → Fehlermeldung nach Template 8.5, Zustand `ERROR`, `simulation_running = false`

---

## 12. Test-Konzept

### 12.1 Framework

- `pytest`
- `pytest-cov` für Coverage

### 12.2 Struktur

- `tests/unit/`: pro Modul eine Testdatei
- `tests/integration/`: End-to-End-Tests der CLI-Interaktion
- `tests/conftest.py`: Fixtures für Config, Battery, Vehicle, Charger, Session, Engine

### 12.3 Coverage-Ziel

- **Domain Layer:** 100 %
- **Config Layer:** 100 %
- **Simulation Layer:** ≥ 90 %
- **CLI Layer:** ≥ 70 %
- **Overall:** ≥ 85 %

### 12.4 Beispieltests (Skizzen)

```python
# tests/unit/test_config.py
def test_set_valid_value_within_range(): ...
def test_set_value_below_min_raises(): ...
def test_set_value_above_max_raises(): ...
def test_set_unknown_key_raises(): ...
def test_bool_parsing_case_insensitive(): ...
def test_reset_restores_defaults(): ...
```

```python
# tests/unit/test_engine.py
def test_effective_power_uses_minimum(): ...
def test_soc_increases_over_ticks(): ...
def test_cooling_activates_above_threshold(): ...
def test_cooling_deactivates_with_hysteresis(): ...
def test_status_transitions_to_completed(): ...
def test_range_calculation(): ...
def test_remaining_time_calculation(): ...
```

```python
# tests/integration/test_cli_flow.py
def test_help_command_output(): ...
def test_show_config_lists_all_parameters(): ...
def test_set_and_show_reflects_change(): ...
def test_start_and_stop_simulation(): ...
```

### 12.5 Nicht Teil der Tests

- Reale Zeitmessungen (`time.sleep` in Tests vermeiden → `speed_factor` extrem hoch setzen oder `tick_seconds` mocken)
- Threading-Details (werden über Integrationstests indirekt abgedeckt)

---

## 13. Nicht funktionale Anforderungen

| Kategorie | Vorgabe |
|-----------|---------|
| Startzeit Container | < 3 s |
| RAM-Verbrauch | < 100 MB |
| CPU-Last idle | < 5 % |
| CPU-Last während Simulation | < 20 % |
| Simulationsdauer 10 → 80 % bei speed_factor=60 | ca. 30–60 s real |

---

## 14. Nicht enthalten (bewusst)

- Persistenz (DB, Files, Volumes)
- Netzwerkschnittstellen
- Farbige CLI-Ausgabe
- Config-Reload zur Laufzeit
- Mehrere Config-Profile
- Multi-Language Support
- Docker HEALTHCHECK
- `requirements.txt`

---

## 15. Architekturentscheidungen (Ergänzung zu Blueprint)

| ID | Entscheidung |
|-----|--------------|
| DEC-009 | Python 3.12, PEP 8, `black` + `ruff` |
| DEC-010 | Src-Layout (`src/ev_battery_monitor/…`) |
| DEC-011 | `threading` (Standardbibliothek), kein asyncio |
| DEC-012 | Logging über `logging`-Modul, stdout, LOG_LEVEL via ENV |
| DEC-013 | `runtime`-Sektion in YAML ist read-only, nicht per `set` änderbar |
| DEC-014 | Cross-Field-Validierung beim `start`-Kommando |
| DEC-015 | Dockerfile ohne Multi-Stage, ohne HEALTHCHECK, Non-root User |
| DEC-016 | Exception-Hierarchie mit `EvBatteryMonitorError` als Root |
| DEC-017 | Dependencies ausschließlich in `pyproject.toml`, keine `requirements.txt` |
| DEC-018 | GitHub Actions unter `.github/workflows/` (`ci.yml`, `docker.yml`) |

---

## 16. Nächste Schritte

1. `pyproject.toml` initialisieren
2. Verzeichnisstruktur inkl. `.github/workflows/` anlegen
3. `config/defaults.yaml` inkl. `runtime`-Sektion committen
4. Dockerfile committen
5. GitHub Actions Workflows (`ci.yml`, `docker.yml`) anlegen
6. Ticket-Serie ableiten (Config → Domain → Engine → CLI → Docker → CI → Tests)
