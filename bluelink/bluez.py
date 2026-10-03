import logging
import time

import dbus
import dbus.mainloop.glib
from gi.repository import GLib

from .audio import AudioManager
from .battery import BatteryMonitor
from .config import Config
from .notifier import Notifier


class BlueZMonitor:
    def __init__(
        self,
        config: Config,
        logger: logging.Logger,
        notifier: Notifier,
        audio_manager: AudioManager,
        battery_monitor: BatteryMonitor,
    ):
        self.config = config
        self.logger = logger
        self.notifier = notifier
        self.audio_manager = audio_manager
        self.battery_monitor = battery_monitor

        self.last_attempt = 0.0
        self._bus = None
        self._device_path: str | None = None

    def connect(self) -> None:
        self.logger.info(
            "Attempting connection to %s",
            self.config.device_mac,
        )

        if self._bus is None or self._device_path is None:
            self.logger.warning(
                "Cannot connect to %s because BlueZ has not exposed the device yet",
                self.config.device_mac,
            )
            return

        try:
            device = self._bus.get_object("org.bluez", self._device_path)
            interface = dbus.Interface(device, "org.bluez.Device1")
            interface.Connect()
        except dbus.DBusException as error:
            self.logger.warning(
                "D-Bus connection request failed for %s: %s",
                self.config.device_mac,
                error,
            )
        else:
            self.logger.info(
                "D-Bus connection request completed for %s",
                self.config.device_mac,
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

        self._device_path = path

        if "BatteryPercentage" in changed:
            self.battery_monitor.update(changed["BatteryPercentage"])

        if any(key in changed for key in ("RSSI", "Connected")):
            if changed.get("Connected", False):
                self.logger.info("Connected successfully")

                self.audio_manager.switch_to_device(self.config.device_mac)

                if self.config.notifications:
                    self.notifier.notify(
                        "Bluetooth device connected",
                        "Your configured Bluetooth audio device is now connected.",
                    )

                return

            GLib.timeout_add(
                self.config.reconnect_delay_ms,
                self.delayed_connect,
            )

    def battery_properties_changed(self, interface, changed, invalidated, path):
        """Handle BlueZ Battery1 updates for the configured device."""
        if interface != "org.bluez.Battery1":
            return
        if not path.endswith(self.config.device_mac.replace(":", "_")):
            return
        if "Percentage" in changed:
            self.battery_monitor.update(changed["Percentage"])

    def run(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self._bus = dbus.SystemBus()

        self._bus.add_signal_receiver(
            self.properties_changed,
            dbus_interface="org.freedesktop.DBus.Properties",
            signal_name="PropertiesChanged",
            arg0="org.bluez.Device1",
            path_keyword="path",
        )
        self._bus.add_signal_receiver(
            self.battery_properties_changed,
            dbus_interface="org.freedesktop.DBus.Properties",
            signal_name="PropertiesChanged",
            arg0="org.bluez.Battery1",
            path_keyword="path",
        )

        self.logger.info("BlueLink started")

        loop = GLib.MainLoop()
        loop.run()
