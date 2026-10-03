"""A small GTK4 status and connection window for BlueLink."""

from __future__ import annotations

import dbus
import gi

from .config import Config

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class BlueLinkApplication(Gtk.Application):
    """Expose the configured device's BlueZ state in a GTK4 window."""

    def __init__(self, config: Config) -> None:
        super().__init__(application_id="io.github.amishkushwaha.BlueLink")
        self._config = config
        self._bus = dbus.SystemBus()
        self._status_label: Gtk.Label | None = None
        self._connect_button: Gtk.Button | None = None
        self.connect("activate", self._on_activate)

    def _on_activate(self, _application: Gtk.Application) -> None:
        window = Gtk.ApplicationWindow(application=self, title="BlueLink")
        window.set_default_size(360, 160)

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        layout.set_margin_top(24)
        layout.set_margin_bottom(24)
        layout.set_margin_start(24)
        layout.set_margin_end(24)

        layout.append(Gtk.Label(label="BlueLink", css_classes=["title-1"]))
        layout.append(Gtk.Label(label=self._config.device_mac))
        self._status_label = Gtk.Label()
        layout.append(self._status_label)

        self._connect_button = Gtk.Button(label="Connect")
        self._connect_button.connect("clicked", self._on_connect_clicked)
        layout.append(self._connect_button)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        layout.append(refresh_button)

        window.set_child(layout)
        self._refresh_status()
        window.present()

    def _find_device(self) -> tuple[object, dict[str, object]] | None:
        manager = dbus.Interface(
            self._bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        for path, interfaces in manager.GetManagedObjects().items():
            properties = interfaces.get("org.bluez.Device1")
            if (
                properties
                and str(properties.get("Address", "")).upper()
                == self._config.device_mac.upper()
            ):
                return path, properties
        return None

    def _refresh_status(self) -> None:
        assert self._status_label is not None
        assert self._connect_button is not None
        try:
            device = self._find_device()
        except dbus.DBusException as error:
            self._status_label.set_text(f"BlueZ is unavailable: {error}")
            self._connect_button.set_sensitive(False)
            return

        if device is None:
            self._status_label.set_text("Device is not currently known to BlueZ.")
            self._connect_button.set_sensitive(False)
            return

        _, properties = device
        connected = bool(properties.get("Connected", False))
        self._status_label.set_text("Connected" if connected else "Disconnected")
        self._connect_button.set_sensitive(not connected)

    def _on_refresh_clicked(self, _button: Gtk.Button) -> None:
        self._refresh_status()

    def _on_connect_clicked(self, _button: Gtk.Button) -> None:
        assert self._status_label is not None
        try:
            device = self._find_device()
            if device is None:
                self._status_label.set_text("Device is not currently known to BlueZ.")
                return
            path, _ = device
            interface = dbus.Interface(
                self._bus.get_object("org.bluez", path),
                "org.bluez.Device1",
            )
            interface.Connect()
            self._status_label.set_text("Connection requested.")
        except dbus.DBusException as error:
            self._status_label.set_text(f"Connection failed: {error}")
        self._refresh_status()


def main() -> int:
    """Start the GTK4 frontend using the same configuration as the daemon."""
    try:
        application = BlueLinkApplication(Config.from_file())
    except (ValueError, dbus.DBusException) as error:
        print(f"BlueLink GUI: {error}")
        return 2
    return application.run(None)
