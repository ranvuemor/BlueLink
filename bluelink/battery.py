"""Bluetooth battery reporting."""

from __future__ import annotations

import logging
from typing import Protocol


class NotificationSender(Protocol):
    def notify(self, title: str, body: str) -> None: ...


class BatteryMonitor:
    """Report battery percentages published by BlueZ's ``Battery1`` interface."""

    def __init__(
        self,
        logger: logging.Logger,
        notifier: NotificationSender,
        enabled: bool = True,
    ) -> None:
        self._logger = logger
        self._notifier = notifier
        self._enabled = enabled
        self._last_percentage: int | None = None

    def update(self, percentage: object) -> None:
        """Record and optionally notify about a newly reported percentage."""
        try:
            value = int(percentage)
        except (TypeError, ValueError):
            self._logger.warning(
                "Ignoring invalid Bluetooth battery value: %r", percentage
            )
            return

        if not 0 <= value <= 100:
            self._logger.warning(
                "Ignoring out-of-range Bluetooth battery value: %d", value
            )
            return
        if value == self._last_percentage:
            return

        self._last_percentage = value
        self._logger.info("Bluetooth device battery: %d%%", value)
        if self._enabled:
            self._notifier.notify("Bluetooth battery", f"Battery level: {value}%.")
