"""Configuration model and validation."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from ev_battery_monitor.exceptions import ConfigKeyError, ConfigValidationError, ConfigValueError


@dataclass(frozen=True)
class Parameter:
    """Single configuration parameter definition."""

    default: Any
    min: Any | None
    max: Any | None
    unit: str
    description: str


class Config:
    """In-memory configuration snapshot."""

    def __init__(self, raw: dict[str, dict[str, dict[str, Any]]]) -> None:
        """Initialize configuration from raw YAML data."""
        self._parameters = self._parse(raw)
        self._defaults = {key: param.default for key, param in self._parameters.items()}
        self._current = deepcopy(self._defaults)

    @property
    def parameters(self) -> dict[str, Parameter]:
        """Return parameter definitions."""
        return self._parameters.copy()

    def get(self, key: str) -> Any:
        """Return the current value for a dotted configuration key."""
        if key not in self._current:
            raise ConfigKeyError(f"Unknown configuration key: {key}")
        return self._current[key]

    def set(self, key: str, value: str) -> None:
        """Set a mutable configuration value from CLI text input."""
        if key not in self._parameters:
            raise ConfigKeyError(f"Unknown configuration key: {key}")
        parameter = self._parameters[key]
        if parameter.min is None and parameter.max is None:
            raise ConfigValueError("runtime parameters are read-only")
        parsed = self._parse_value(key, value, type(parameter.default))
        if parameter.min is not None and parsed < parameter.min:
            raise ConfigValueError(self._format_expected(key, value, parameter))
        if parameter.max is not None and parsed > parameter.max:
            raise ConfigValueError(self._format_expected(key, value, parameter))
        self._current[key] = parsed

    def reset(self) -> None:
        """Restore the frozen YAML defaults."""
        self._current = deepcopy(self._defaults)

    def rows(self) -> list[tuple[str, Any, Any, Any, Any, str]]:
        """Return rows suitable for show-config rendering."""
        return [
            (key, param.default, param.min, param.max, self._current[key], param.unit)
            for key, param in sorted(self._parameters.items())
        ]

    def validate_for_start(self) -> None:
        """Validate cross-field constraints before starting a simulation."""
        if self.get("battery.start_soc_percent") >= self.get("session.target_soc_percent"):
            raise ConfigValidationError(
                "battery.start_soc_percent must be lower than session.target_soc_percent"
            )
        if self.get("battery.start_temperature_celsius") >= (
            self.get("session.cooling_threshold_celsius") + 20
        ):
            raise ConfigValidationError(
                "battery.start_temperature_celsius must be lower than "
                "session.cooling_threshold_celsius + 20"
            )
        if self.get("charger.max_power_kw") <= 0:
            raise ConfigValidationError("charger.max_power_kw must be greater than 0")
        if self.get("vehicle.max_charging_power_kw") <= 0:
            raise ConfigValidationError("vehicle.max_charging_power_kw must be greater than 0")

    @staticmethod
    def _parse(raw: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Parameter]:
        parsed = {}
        for section, values in raw.items():
            for name, data in values.items():
                parsed[f"{section}.{name}"] = Parameter(
                    default=data["default"],
                    min=data.get("min"),
                    max=data.get("max"),
                    unit=str(data.get("unit", "")),
                    description=str(data.get("description", "")),
                )
        return parsed

    def _parse_value(self, key: str, value: str, target_type: type[Any]) -> Any:
        try:
            if target_type is bool:
                if value.lower() in {"true", "false"}:
                    return value.lower() == "true"
                raise ValueError
            if target_type is float:
                return float(value)
            if target_type is int:
                return int(value)
            return value
        except ValueError as exc:
            param = self._parameters[key]
            raise ConfigValueError(self._format_expected(key, value, param)) from exc

    @staticmethod
    def _format_expected(key: str, value: str, parameter: Parameter) -> str:
        expected = type(parameter.default).__name__
        return (
            f"Invalid value '{value}' for {key}\n"
            f"Expected type: {expected} ({parameter.min} – {parameter.max})"
        )
