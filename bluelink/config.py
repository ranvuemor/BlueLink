from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    device_mac: str
    reconnect_delay_ms: int = 1000
    cooldown_seconds: int = 5
    notifications: bool = True