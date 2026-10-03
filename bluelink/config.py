"""Configuration loading for BlueLink."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "bluelink" / "config.toml"


@dataclass(slots=True)
class Config:
    device_mac: str
    reconnect_delay_ms: int = 1000
    cooldown_seconds: int = 5
    audio_retry_count: int = 10
    audio_retry_delay: float = 0.5
    notifications: bool = True
    battery_notifications: bool = True

    @classmethod
    def from_file(cls, path: Path = DEFAULT_CONFIG_PATH) -> Config:
        """Load a BlueLink TOML configuration file.

        The device MAC address is the sole required setting.  Unknown keys are
        rejected so misspelled options cannot silently alter daemon behaviour.
        """
        try:
            with path.open("rb") as config_file:
                values = tomllib.load(config_file)
        except FileNotFoundError as error:
            raise ValueError(f"Configuration file not found: {path}") from error
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"Invalid TOML in {path}: {error}") from error

        valid_keys = set(cls.__dataclass_fields__)
        unknown_keys = set(values) - valid_keys
        if unknown_keys:
            unknown = ", ".join(sorted(unknown_keys))
            raise ValueError(f"Unknown configuration option(s): {unknown}")

        try:
            config = cls(**values)
        except TypeError as error:
            raise ValueError(f"Invalid configuration in {path}: {error}") from error

        if not config.device_mac:
            raise ValueError("device_mac cannot be empty")
        if config.reconnect_delay_ms < 0:
            raise ValueError("reconnect_delay_ms cannot be negative")
        if config.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")
        if config.audio_retry_count < 1:
            raise ValueError("audio_retry_count must be at least 1")
        if config.audio_retry_delay < 0:
            raise ValueError("audio_retry_delay cannot be negative")

        return config
