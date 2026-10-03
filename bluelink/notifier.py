"""Best-effort desktop notifications."""

import logging

import dbus


class Notifier:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("bluelink")
        self.interface = None
        try:
            bus = dbus.SessionBus()
            notification_service = bus.get_object(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
            )
            self.interface = dbus.Interface(
                notification_service,
                "org.freedesktop.Notifications",
            )
        except dbus.DBusException:
            self._logger.warning("Desktop notifications are unavailable")

    def notify(self, title: str, body: str) -> None:
        if self.interface is None:
            return
        self.interface.Notify(
            "BlueLink",  # app name
            0,  # replaces id
            "audio-headphones",
            title,
            body,
            [],
            {},
            3000,
        )
