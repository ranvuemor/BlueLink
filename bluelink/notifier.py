import dbus


class Notifier:
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.notify = self.bus.get_object(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
        )

        self.interface = dbus.Interface(
            self.notify,
            "org.freedesktop.Notifications",
        )

    def notify(self, title: str, body: str) -> None:
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
