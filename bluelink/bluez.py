import logging
import subprocess
import time

import dbus
import dbus.mainloop.glib
from gi.repository import GLib

from .audio import AudioManager
from .config import Config
from .notifier import Notifier


class BlueZMonitor:
    def __init__(
        self,
        config: Config,
        logger: logging.Logger,
        notifier: Notifier,
        audio_manager: AudioManager,
    ):
        self.config = config
        self.logger = logger
        self.notifier = notifier
        self.audio_manager = audio_manager

        self.last_attempt = 0.0

    def connect(self) -> None:
        self.logger.info(
            "Attempting connection to %s",
            self.config.device_mac,
        )

        result = subprocess.run(
            ["bluetoothctl", "connect", self.config.device_mac],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        if result.returncode == 0:
            self.logger.info(
                "Connection command completed for %s",
                self.config.device_mac,
            )
        else:
            self.logger.warning(
                "Connection command failed for %s (exit code %d)",
                self.config.device_mac,
                result.returncode,
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
                self.logger.info("Connected successfully")

                self.audio_manager.switch_to_bluetooth_sink(self.config.device_mac)

                if self.config.notifications:
                    self.notifier.notify(
                        "🎧 AirPods Connected",
                        "Amish's AirPods Pro is now connected.",
                    )

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
