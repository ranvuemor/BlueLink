import logging
import subprocess
import unittest

from bluelink.audio import AudioManager


class FakeNotifier:
    def __init__(self) -> None:
        self.notifications: list[tuple[str, str]] = []

    def notify(self, title: str, body: str) -> None:
        self.notifications.append((title, body))


class FakePactl:
    def __init__(self, responses: list[subprocess.CompletedProcess[str]]) -> None:
        self.commands: list[list[str]] = []
        self._responses = responses

    def __call__(
        self,
        command: list[str],
        **_: object,
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        return self._responses.pop(0)


def completed(
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["pactl"], returncode, stdout, stderr)


class AudioManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.notifier = FakeNotifier()
        self.logger = logging.getLogger("bluelink.tests.audio")

    def test_switches_default_sink_and_moves_every_stream(self) -> None:
        sink = "bluez_output.98_A5_F9_25_83_9B.1"
        pactl = FakePactl(
            [
                completed(stdout=f"42\t{sink}\tPipeWire\ts16le\n"),
                completed(),
                completed(
                    stdout="7\t42\tprotocol-native.c\n8\t42\tprotocol-native.c\n"
                ),
                completed(),
                completed(),
            ]
        )
        manager = AudioManager(self.logger, self.notifier, pactl)

        switched = manager.switch_to_bluetooth_sink("98:A5:F9:25:83:9B")

        self.assertTrue(switched)
        self.assertEqual(
            pactl.commands,
            [
                ["pactl", "list", "short", "sinks"],
                ["pactl", "set-default-sink", sink],
                ["pactl", "list", "short", "sink-inputs"],
                ["pactl", "move-sink-input", "7", sink],
                ["pactl", "move-sink-input", "8", sink],
            ],
        )
        self.assertEqual(self.notifier.notifications[0][0], "Audio switched")

    def test_notifies_when_the_bluetooth_sink_is_unavailable(self) -> None:
        pactl = FakePactl([completed(stdout="42\talsa_output.pci-0000\tPipeWire\n")])
        manager = AudioManager(self.logger, self.notifier, pactl)

        switched = manager.switch_to_bluetooth_sink("98:A5:F9:25:83:9B")

        self.assertFalse(switched)
        self.assertEqual(
            self.notifier.notifications,
            [
                (
                    "Audio switching failed",
                    "Bluetooth audio output is not available yet.",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
