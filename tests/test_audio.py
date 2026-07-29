import logging
import subprocess
import unittest
from unittest.mock import Mock, call

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

    def test_finds_the_sink_immediately_and_moves_every_stream(self) -> None:
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
        sleeper = Mock()
        manager = AudioManager(self.logger, self.notifier, pactl, sleeper=sleeper)

        switched = manager.switch_to_device("98:A5:F9:25:83:9B")

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
        sleeper.assert_not_called()
        self.assertEqual(self.notifier.notifications[0][0], "Audio switched")

    def test_finds_the_sink_after_several_retries(self) -> None:
        sink = "bluez_output.98_A5_F9_25_83_9B.1"
        pactl = FakePactl(
            [
                completed(stdout="42\talsa_output.pci-0000\tPipeWire\n"),
                completed(stdout="42\talsa_output.pci-0000\tPipeWire\n"),
                completed(stdout=f"43\t{sink}\tPipeWire\n"),
                completed(),
                completed(),
            ]
        )
        sleeper = Mock()
        manager = AudioManager(
            self.logger,
            self.notifier,
            pactl,
            retry_delay=0.5,
            sleeper=sleeper,
        )

        switched = manager.switch_to_device("98:A5:F9:25:83:9B")

        self.assertTrue(switched)
        self.assertEqual(sleeper.call_args_list, [call(0.5), call(0.5)])
        self.assertEqual(self.notifier.notifications[0][0], "Audio switched")

    def test_notifies_only_after_the_sink_never_appears(self) -> None:
        pactl = FakePactl(
            [
                completed(stdout="42\talsa_output.pci-0000\tPipeWire\n"),
                completed(stdout="42\talsa_output.pci-0000\tPipeWire\n"),
                completed(stdout="42\talsa_output.pci-0000\tPipeWire\n"),
            ]
        )
        sleeper = Mock()
        manager = AudioManager(
            self.logger,
            self.notifier,
            pactl,
            retry_count=3,
            sleeper=sleeper,
        )

        switched = manager.switch_to_device("98:A5:F9:25:83:9B")

        self.assertFalse(switched)
        self.assertEqual(sleeper.call_count, 2)
        self.assertEqual(
            self.notifier.notifications,
            [
                (
                    "Audio switching failed",
                    "Bluetooth audio output is not available yet.",
                )
            ],
        )

    def test_respects_the_configured_retry_count(self) -> None:
        pactl = FakePactl(
            [completed(stdout="42\talsa_output.pci-0000\tPipeWire\n")] * 4
        )
        sleeper = Mock()
        manager = AudioManager(
            self.logger,
            self.notifier,
            pactl,
            retry_count=4,
            sleeper=sleeper,
        )

        manager.switch_to_device("98:A5:F9:25:83:9B")

        self.assertEqual(pactl.commands, [["pactl", "list", "short", "sinks"]] * 4)
        self.assertEqual(sleeper.call_count, 3)


if __name__ == "__main__":
    unittest.main()
