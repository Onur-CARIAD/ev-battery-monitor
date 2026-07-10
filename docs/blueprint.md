# EV Battery Monitoring Service – Blueprint Release 1

**Version:** 1.1
**Status:** Draft
**Scope:** Release 1 (personal use, single container)
**Companion Document:** `technical-spec.md`

---

## 1. Zielsetzung

Der EV Battery Monitoring Service simuliert einen Ladevorgang eines Elektrofahrzeugs und gibt dem Nutzer die wichtigsten Batterieparameter in Echtzeit auf der Konsole aus.

Die App läuft in einem Docker Container und ist per **One Command Startup** interaktiv über die CLI bedienbar.

Ziele von Release 1:

- Überschaubare Komplexität
- Vollständig testbar
- Docker-fähig
- Grundlage für spätere Erweiterungen (Ladekurven, Zelltemperaturen, Web-UI, etc.)

---

## 2. Fachliche Anforderungen

### 2.1 Eingabedaten (vom Nutzer konfigurierbar)

- Batteriekapazität
- Start-SoC
- Start-Batterietemperatur
- Maximale Ladeleistung Fahrzeug
- Verbrauch (kWh / 100 km)
- Maximale Ladeleistung Ladesäule
- Ziel-SoC
- Kühlung an/aus, Schwellwert, Kühlleistung

### 2.2 Simulierte Ausgaben

- Aktueller SoC
- Aktuelle Batterietemperatur
- Aktuelle Ladeleistung
- Reichweite
- Kühlungsstatus
- Ladezustand (Charging Status)
- Verbleibende Ladezeit

### 2.3 Nicht persistente Daten

Simulationswerte werden nicht gespeichert. Sie existieren nur zur Laufzeit im `SimulationState`.

---

## 3. Domain-Modell

### 3.1 Entitäten und Attribute

#### Battery

| Attribut | Typ | Default | Min | Max | Unit |
|-----------|------|---------|------|------|------|
| capacity_kwh | float | 77.0 | 20.0 | 200.0 | kWh |
| start_soc_percent | float | 10.0 | 0.0 | 100.0 | % |
| start_temperature_celsius | float | 25.0 | -20.0 | 60.0 | °C |

#### Vehicle

| Attribut | Typ | Default | Min | Max | Unit |
|-----------|------|---------|------|------|------|
| max_charging_power_kw | float | 135.0 | 10.0 | 400.0 | kW |
| consumption_kwh_per_100km | float | 18.0 | 8.0 | 40.0 | kWh/100km |

#### Charger

| Attribut | Typ | Default | Min | Max | Unit |
|-----------|------|---------|------|------|------|
| max_power_kw | float | 300.0 | 3.7 | 400.0 | kW |

#### ChargingSession

| Attribut | Typ | Default | Min | Max | Unit |
|-----------|------|---------|------|------|------|
| target_soc_percent | float | 80.0 | 1.0 | 100.0 | % |
| cooling_enabled | bool | true | false | true | bool |
| cooling_threshold_celsius | float | 40.0 | 20.0 | 60.0 | °C |
| cooling_power_kw | float | 5.0 | 0.0 | 20.0 | kW |

### 3.2 Objektbeziehungen

```text
ChargingSession
├── Battery
├── Vehicle
└── Charger
```

---

## 4. Simulationsregeln

### 4.1 Grundprinzip

- Simulation läuft in festen Ticks (z. B. 1 Sekunde).
- Ein `speed_factor` beschleunigt die Simulation (z. B. 60 = 1 Sekunde real = 60 Sekunden simuliert).
- Alle Regeln sind deterministisch.

### 4.2 Effektive Ladeleistung

```text
P_base = min(Vehicle.max_charging_power_kw, Charger.max_power_kw)

wenn Kühlung aktiv:
    P_effective = P_base - cooling_power_kw
sonst:
    P_effective = P_base
```

Kein Rauschen.

### 4.3 SoC-Anstieg pro Tick

```text
energy_per_tick_kwh = P_effective * (tick_seconds / 3600) * speed_factor

delta_soc_percent  = (energy_per_tick_kwh / Battery.capacity_kwh) * 100

current_soc = current_soc + delta_soc_percent   (begrenzt auf [0, target_soc])
```

### 4.4 Temperaturmodell

```text
delta_temp_heating = P_effective * heating_factor          # heating_factor = 0.0008 °C/kW/Tick

wenn Kühlung aktiv:
    delta_temp_cooling = -0.15 °C
sonst:
    delta_temp_cooling = 0

current_temp = current_temp + delta_temp_heating + delta_temp_cooling
```

Keine passive Abkühlung Richtung Umgebung.

### 4.5 Kühlungslogik (Hysterese)

```text
Kühlung EIN, wenn current_temp >= cooling_threshold_celsius
Kühlung AUS, wenn current_temp <= (cooling_threshold_celsius - 3 °C)
```

### 4.6 Reichweite

```text
available_energy_kwh = Battery.capacity_kwh * (current_soc / 100)
range_km             = (available_energy_kwh / consumption_kwh_per_100km) * 100
```

### 4.7 Charging Status (State Machine)

```text
IDLE      → CHARGING   (bei Start)
CHARGING  → COOLING    (Temperatur > Schwelle)
CHARGING  → COMPLETED  (SoC >= Target)
COOLING   → CHARGING   (Temperatur < Schwelle - 3 °C)
COOLING   → COMPLETED  (SoC >= Target)
COMPLETED → (Ende)
ERROR     → (bei Exception)
```

### 4.8 Verbleibende Zeit

```text
remaining_soc       = target_soc - current_soc
remaining_energy    = (remaining_soc / 100) * Battery.capacity_kwh
remaining_time_min  = (remaining_energy / P_effective) * 60
```

### 4.9 Ausgabe-Trigger

Ausgabe erfolgt:

- Wenn sich SoC um mindestens 1 % erhöht hat
- Bei Statuswechsel (CHARGING ↔ COOLING, → COMPLETED)
- Bei Simulationsstart und -ende
- Bei `stop`-Kommando oder Fehlerfall

---

## 5. Architektur

### 5.1 Übersicht

```text
+---------------------------------+
| Docker Container                |
|                                 |
|  +---------------------------+  |
|  | 1. Config Layer           |  |
|  |    YAML + CLI Overrides   |  |
|  +-------------+-------------+  |
|                v                |
|  +---------------------------+  |
|  | 2. Domain Layer           |  |
|  |    Battery, Vehicle,      |  |
|  |    Charger, Session       |  |
|  +-------------+-------------+  |
|                v                |
|  +---------------------------+  |
|  | 3. Simulation Layer       |  |
|  |    SimulationEngine       |  |
|  |    -> SimulationState     |  |
|  +-------------+-------------+  |
|                v                |
|  +---------------------------+  |
|  | 4. Interface Layer        |  |
|  |    Console CLI            |  |
|  +---------------------------+  |
|                                 |
+---------------------------------+
```

### 5.2 Config Layer

- Defaults werden aus `config/defaults.yaml` geladen.
- YAML wird ins Docker Image kopiert (build time).
- Werte sind zur Laufzeit in-memory änderbar über `set`.
- Änderungen leben nur bis `exit`.
- Kein Editor, keine YAML-Bearbeitung zur Laufzeit.

### 5.3 Interface Layer

- Rein Console-basiert.
- Kein FastAPI.
- Kein exponierter Port.
- Keine Statusdatei.
- Keine Farben.
- Kein `help set`.

---

## 6. CLI-Kommandos

| Kommando | Beschreibung |
|-----------|--------------|
| `help` | Übersicht aller Kommandos |
| `show config` | Zeigt Parameter mit Default / Min / Max / Current / Unit |
| `set <key> <val>` | Ändert einen Wert (mit Validierung gegen Min/Max) |
| `reset config` | Zurück auf Defaults aus YAML |
| `start` | Simulation starten |
| `stop` | Laufende Simulation abbrechen |
| `metrics` | Technische und letzte Simulationsmetriken |
| `exit` | App beenden |

Während laufender Simulation ist nur `stop` erlaubt.

---

## 7. Metriken

### 7.1 Technische Metriken

- `uptime_seconds`
- `tick_count_total`
- `tick_duration_ms`
- `simulation_running` (bool)

### 7.2 Fachliche Metriken

- `current_soc_percent`
- `current_temperature_celsius`
- `current_charging_power_kw`
- `current_range_km`
- `cooling_active` (bool)
- `charging_status`

### 7.3 Fehlerfall

Bei unerwartetem Abbruch der Simulation:

- Exception fangen
- Fehlermeldung ausgeben
- Letzten `SimulationState` anzeigen
- `simulation_running = false`
- Rückkehr in CLI-Menü

---

## 8. Docker

- One command startup: `docker run -it ev-battery-monitor`
- Interaktive Session über `-it`
- Keine Volumes nötig
- Keine Ports nötig
- YAML wird beim Build ins Image kopiert
- Kein Docker Healthcheck-Endpoint in Release 1

---

## 9. Blueprint-Skizzen der Klassen

Nur Attribute und Methodensignaturen. Keine Implementierung.

### 9.1 Domain-Klassen

```python
# domain/battery.py
class Battery:
    capacity_kwh: float
    start_soc_percent: float
    start_temperature_celsius: float

    def __init__(
        self,
        capacity_kwh: float,
        start_soc_percent: float,
        start_temperature_celsius: float,
    ) -> None: ...
```

```python
# domain/vehicle.py
class Vehicle:
    max_charging_power_kw: float
    consumption_kwh_per_100km: float

    def __init__(
        self,
        max_charging_power_kw: float,
        consumption_kwh_per_100km: float,
    ) -> None: ...
```

```python
# domain/charger.py
class Charger:
    max_power_kw: float

    def __init__(self, max_power_kw: float) -> None: ...
```

```python
# domain/charging_session.py
class ChargingSession:
    target_soc_percent: float
    cooling_enabled: bool
    cooling_threshold_celsius: float
    cooling_power_kw: float

    battery: Battery
    vehicle: Vehicle
    charger: Charger

    def __init__(
        self,
        battery: Battery,
        vehicle: Vehicle,
        charger: Charger,
        target_soc_percent: float,
        cooling_enabled: bool,
        cooling_threshold_celsius: float,
        cooling_power_kw: float,
    ) -> None: ...
```

### 9.2 Config

```python
# config/config_loader.py
class ConfigLoader:
    def load_defaults(self, path: str) -> dict: ...
```

```python
# config/config.py
class Config:
    def get(self, key: str) -> float | bool: ...
    def set(self, key: str, value: float | bool) -> None: ...
    def reset(self) -> None: ...
    def validate(self, key: str, value: float | bool) -> bool: ...
    def as_dict(self) -> dict: ...
    def describe(self) -> list: ...   # fuer "show config"
```

### 9.3 SimulationState

```python
# simulation/state.py
class SimulationState:
    tick_number: int
    timestamp: datetime

    soc_percent: float
    temperature_celsius: float
    charging_power_kw: float
    range_km: float

    status: str            # IDLE | CHARGING | COOLING | COMPLETED | ERROR
    cooling_active: bool
    remaining_time_min: float
```

### 9.4 SimulationEngine

```python
# simulation/engine.py
class SimulationEngine:
    session: ChargingSession
    state: SimulationState

    tick_seconds: float
    speed_factor: float
    heating_factor: float

    running: bool
    stop_requested: bool

    def __init__(
        self,
        session: ChargingSession,
        tick_seconds: float,
        speed_factor: float,
    ) -> None: ...

    # Lifecycle
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...

    # Simulation
    def tick(self) -> SimulationState: ...
    def _calculate_effective_power(self) -> float: ...
    def _update_soc(self, p_effective: float) -> None: ...
    def _update_temperature(self, p_effective: float) -> None: ...
    def _update_cooling_state(self) -> None: ...
    def _update_status(self) -> None: ...
    def _calculate_range(self) -> float: ...
    def _calculate_remaining_time(self, p_effective: float) -> float: ...

    # Output-Trigger
    def _should_emit_output(self, previous_state: SimulationState) -> bool: ...
```

### 9.5 Metrics

```python
# metrics/metrics.py
class Metrics:
    uptime_seconds: float
    tick_count_total: int
    tick_duration_ms: float
    simulation_running: bool

    def start_uptime(self) -> None: ...
    def record_tick(self, duration_ms: float) -> None: ...
    def snapshot(self) -> dict: ...
```

### 9.6 CLI

```python
# cli/cli.py
class CLI:
    config: Config
    engine: SimulationEngine | None
    metrics: Metrics

    def run(self) -> None: ...              # Haupt-Loop

    # Command Handler
    def cmd_help(self) -> None: ...
    def cmd_show_config(self) -> None: ...
    def cmd_set(self, key: str, value: str) -> None: ...
    def cmd_reset_config(self) -> None: ...
    def cmd_start(self) -> None: ...
    def cmd_stop(self) -> None: ...
    def cmd_metrics(self) -> None: ...
    def cmd_exit(self) -> None: ...

    # Ausgabe
    def print_state(self, state: SimulationState) -> None: ...
    def print_error(self, message: str, state: SimulationState | None) -> None: ...
```

### 9.7 App Entry Point

```python
# main.py
def main() -> None: ...
```

---

## 10. Abgrenzung Release 1

**Nicht enthalten:**

- Zellspannungen
- Einzelzelltemperaturen
- Batteriedegradation / SOH
- Realistische Ladekurven
- Außentemperatur
- Rekuperation / Fahrbetrieb
- FastAPI / Web-UI
- Persistenz (DB, JSON, Volumes)
- Docker Healthcheck-Endpoint
- Farbige CLI-Ausgabe
- Mehrere Config-Profile

---

## 11. Architekturentscheidungen

| ID | Entscheidung |
|-----|--------------|
| DEC-001 | Defaults werden aus `config/defaults.yaml` geladen (statisch, versioniert, build time) |
| DEC-002 | CLI-Overrides ausschließlich über `set <key> <value>` mit Validierung gegen Min/Max |
| DEC-003 | Simulation deterministisch (kein Rauschen, keine passive Abkühlung) |
| DEC-004 | 4-Schichten-Architektur: Config / Domain / Simulation / Interface |
| DEC-005 | Interface Layer ist Console-only (kein FastAPI, keine Ports, keine Statusdatei) |
| DEC-006 | Ausgabe pro +1 % SoC + bei Statuswechseln + Start/Ende/Stop/Fehler |
| DEC-007 | `stop` während Simulation über separaten Input-Thread |
| DEC-008 | Metriken (technisch + fachlich) über CLI-Kommando `metrics` abfragbar |

Technische Architekturentscheidungen (DEC-009 bis DEC-018) siehe `technical-spec.md`.

---

## 12. Nächste Schritte

1. User Stories und Tickets im Repo anlegen
2. Projektstruktur (`config/`, `domain/`, `simulation/`, `cli/`, `metrics/`, `tests/`, `.github/workflows/`) initialisieren
3. `config/defaults.yaml` committen
4. Dockerfile skizzieren
5. Unit-Test-Grundlage aufsetzen
6. Für alle technischen Details siehe `technical-spec.md`
