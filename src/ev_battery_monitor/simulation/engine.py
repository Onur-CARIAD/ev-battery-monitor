"""Tick-based charging simulation engine."""

from ev_battery_monitor.config.config import Config
from ev_battery_monitor.domain.battery import Battery
from ev_battery_monitor.domain.charger import Charger
from ev_battery_monitor.domain.charging_session import ChargingSession
from ev_battery_monitor.domain.vehicle import Vehicle
from ev_battery_monitor.exceptions import SimulationRuntimeError
from ev_battery_monitor.simulation.state import SimulationState, SimulationStatus


class SimulationEngine:
    """Runs charging simulation ticks."""

    def __init__(
        self,
        battery: Battery,
        vehicle: Vehicle,
        charger: Charger,
        session: ChargingSession,
        config: Config,
    ) -> None:
        """Initialize the engine with domain objects and runtime configuration."""
        self.battery = battery
        self.vehicle = vehicle
        self.charger = charger
        self.session = session
        self.config = config
        self.cooling = False
        self.tick_count = 0
        self.last_state = self._state(0.0, SimulationStatus.CHARGING)

    @classmethod
    def from_config(cls, config: Config) -> "SimulationEngine":
        """Create an engine from application configuration."""
        return cls(
            battery=Battery(
                capacity_kwh=config.get("battery.capacity_kwh"),
                soc_percent=config.get("battery.start_soc_percent"),
                temperature_celsius=config.get("battery.start_temperature_celsius"),
                range_per_kwh_km=config.get("battery.range_per_kwh_km"),
            ),
            vehicle=Vehicle(config.get("vehicle.max_charging_power_kw")),
            charger=Charger(config.get("charger.max_power_kw")),
            session=ChargingSession(
                target_soc_percent=config.get("session.target_soc_percent"),
                cooling_threshold_celsius=config.get("session.cooling_threshold_celsius"),
                cooling_power_reduction_factor=config.get("session.cooling_power_reduction_factor"),
            ),
            config=config,
        )

    def tick(self) -> SimulationState:
        """Advance the simulation by one tick."""
        try:
            if self.battery.soc_percent >= self.session.target_soc_percent:
                self.last_state = self._state(0.0, SimulationStatus.COMPLETED)
                return self.last_state

            self._update_cooling()
            power = self.effective_power_kw()
            tick_seconds = self.config.get("runtime.tick_seconds")
            speed_factor = self.config.get("runtime.speed_factor")
            simulated_hours = (tick_seconds * speed_factor) / 3600.0
            self.battery.add_energy(power * simulated_hours)
            self.battery.soc_percent = min(
                self.battery.soc_percent, self.session.target_soc_percent
            )
            self.battery.heat(power * self.config.get("runtime.heating_factor"))
            self.tick_count += 1
            status = SimulationStatus.COOLING if self.cooling else SimulationStatus.CHARGING
            if self.battery.soc_percent >= self.session.target_soc_percent:
                status = SimulationStatus.COMPLETED
                power = 0.0
            self.last_state = self._state(power, status)
            return self.last_state
        except Exception as exc:
            self.last_state.status = SimulationStatus.ERROR
            raise SimulationRuntimeError(str(exc)) from exc

    def effective_power_kw(self) -> float:
        """Return effective charging power for the current tick."""
        power = min(self.vehicle.max_charging_power_kw, self.charger.max_power_kw)
        if self.cooling:
            power *= self.session.cooling_power_reduction_factor
        return power

    def remaining_time_seconds(self) -> float:
        """Estimate remaining real seconds until target SoC."""
        remaining_percent = max(0.0, self.session.target_soc_percent - self.battery.soc_percent)
        remaining_kwh = self.battery.capacity_kwh * remaining_percent / 100.0
        power = max(self.effective_power_kw(), 0.001)
        real_hours = (remaining_kwh / power) / self.config.get("runtime.speed_factor")
        return real_hours * 3600.0

    def _update_cooling(self) -> None:
        if self.battery.temperature_celsius >= self.session.cooling_threshold_celsius:
            self.cooling = True
        elif self.battery.temperature_celsius <= (
            self.session.cooling_threshold_celsius
            - self.config.get("runtime.cooling_hysteresis_celsius")
        ):
            self.cooling = False

    def _state(self, power: float, status: SimulationStatus) -> SimulationState:
        return SimulationState(
            soc_percent=self.battery.soc_percent,
            temperature_celsius=self.battery.temperature_celsius,
            charging_power_kw=power,
            range_km=self.battery.estimated_range_km(),
            cooling=self.cooling,
            status=status,
            tick_count=self.tick_count,
        )
