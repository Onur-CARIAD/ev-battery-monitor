"""Application exception hierarchy."""


class EvBatteryMonitorError(Exception):
    """Base error for EV Battery Monitor."""


class ConfigError(EvBatteryMonitorError):
    """Base error for configuration problems."""


class ConfigKeyError(ConfigError):
    """Raised when an unknown configuration key is requested."""


class ConfigValueError(ConfigError):
    """Raised when a configuration value is invalid."""


class ConfigValidationError(ConfigError):
    """Raised when cross-field validation fails."""


class SimulationError(EvBatteryMonitorError):
    """Base error for simulation problems."""


class SimulationStateError(SimulationError):
    """Raised when the simulation state is invalid."""


class SimulationRuntimeError(SimulationError):
    """Raised when a simulation tick fails unexpectedly."""
