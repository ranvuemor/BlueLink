import subprocess
import time
import logging

import dbus
import dbus.mainloop.glib
from gi.repository import GLib

from .config import Config
from .notifier import Notifier


class BlueZMonitor:
    def __init__(
        self,
        config: Config,
        logger: logging.Logger,
        notifier: Notifier,
    ):
        self.config = config
        self.logger = logger
        self.notifier = notifier

        self.last_attempt = 0.0

    def connect(self) -> None:
        self.logger.info("Attempting connection to %s", self.config.device_mac)

        subprocess.run(
            ["bluetoothctl", "connect", self.config.device_mac],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def delayed_connect(self):
        now = time.monotonic()

        if now - self.last_attempt < self.config.cooldown_seconds:
            return False

        self.last_attempt = now

        self.connect()

        return False

    def properties_changed(self, interface, changed, invalidated, path):
        if interface != "org.bluez.Device1":
            return

        if not path.endswith(self.config.device_mac.replace(":", "_")):
            return

        if any(key in changed for key in ("RSSI", "Connected")):
            if changed.get("Connected", False):
                self.logger.info("Device connected")
                return

            GLib.timeout_add(
                self.config.reconnect_delay_ms,
                self.delayed_connect,
            )

    def run(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        bus = dbus.SystemBus()

        bus.add_signal_receiver(
            self.properties_changed,
            dbus_interface="org.freedesktop.DBus.Properties",
            signal_name="PropertiesChanged",
            arg0="org.bluez.Device1",
            path_keyword="path",
        )

        self.logger.info("BlueLink started")

        loop = GLib.MainLoop()
        loop.run()