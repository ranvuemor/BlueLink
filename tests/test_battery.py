import logging
import unittest

from bluelink.battery import BatteryMonitor


class FakeNotifier:
    def __init__(self) -> None:
        self.notifications: list[tuple[str, str]] = []

    def notify(self, title: str, body: str) -> None:
        self.notifications.append((title, body))


class BatteryMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.notifier = FakeNotifier()
        self.monitor = BatteryMonitor(
            logging.getLogger("bluelink.tests.battery"), self.notifier
        )

    def test_notifies_when_the_battery_changes(self) -> None:
        self.monitor.update(85)
        self.monitor.update(85)
        self.monitor.update("84")

        self.assertEqual(
            self.notifier.notifications,
            [
                ("Bluetooth battery", "Battery level: 85%."),
                ("Bluetooth battery", "Battery level: 84%."),
            ],
        )

    def test_ignores_invalid_battery_values(self) -> None:
        self.monitor.update(-1)
        self.monitor.update(101)
        self.monitor.update("unknown")

        self.assertEqual(self.notifier.notifications, [])

    def test_can_disable_battery_notifications(self) -> None:
        monitor = BatteryMonitor(
            logging.getLogger("bluelink.tests.battery"),
            self.notifier,
            enabled=False,
        )

        monitor.update(85)

        self.assertEqual(self.notifier.notifications, [])


if __name__ == "__main__":
    unittest.main()
