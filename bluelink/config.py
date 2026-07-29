from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    device_mac: str
    reconnect_delay_ms: int = 1000
    cooldown_seconds: int = 5
    audio_retry_count: int = 10
    audio_retry_delay: float = 0.5
    notifications: bool = True
