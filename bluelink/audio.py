"""Audio-routing support for Bluetooth devices."""

from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Callable
from typing import Protocol

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
Sleeper = Callable[[float], None]


class NotificationSender(Protocol):
    """The notification capability required by :class:`AudioManager`."""

    def notify(self, title: str, body: str) -> None:
        """Show a desktop notification."""


class AudioManager:
    """Switch PulseAudio/PipeWire audio streams to a connected Bluetooth device.

    PipeWire exposes its PulseAudio-compatible control API through ``pactl``, so
    this works for both PulseAudio and a typical PipeWire desktop session.
    """

    def __init__(
        self,
        logger: logging.Logger,
        notifier: NotificationSender,
        command_runner: CommandRunner | None = None,
        retry_count: int = 10,
        retry_delay: float = 0.5,
        sleeper: Sleeper | None = None,
    ) -> None:
        if retry_count < 1:
            raise ValueError("retry_count must be at least 1")
        if retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")

        self._logger = logger
        self._notifier = notifier
        self._command_runner = command_runner or subprocess.run
        self._retry_count = retry_count
        self._retry_delay = retry_delay
        self._sleeper = sleeper or time.sleep

    def switch_to_device(self, device_mac: str) -> bool:
        """Make *device_mac*'s sink default and move active streams to it."""
        try:
            return self._switch_to_device(device_mac)
        except Exception:
            self._logger.exception("Unexpected error while switching Bluetooth audio")
            self._notify_failure("An unexpected error occurred while switching audio.")
            return False

    def _switch_to_device(self, device_mac: str) -> bool:
        """Perform the audio switch after the public failure boundary."""
        self._logger.info("Switching audio to Bluetooth device %s", device_mac)

        sink = self._wait_for_sink(device_mac)
        if sink is None:
            self._notify_failure("Bluetooth audio output is not available yet.")
            return False

        if not self._set_default_sink(sink):
            self._notify_failure("Could not set the Bluetooth audio output.")
            return False

        if not self._move_active_streams(sink):
            self._notify_failure("Could not move all active audio streams.")
            return False

        self._logger.info("Audio switched successfully to sink %s", sink)
        self._notify(
            "Audio switched",
            "Audio is now playing through your Bluetooth device.",
        )
        return True

    def _wait_for_sink(self, mac: str) -> str | None:
        """Wait for PipeWire or PulseAudio to expose the Bluetooth sink."""
        self._logger.info("Waiting for Bluetooth audio sink for %s", mac)

        for attempt in range(1, self._retry_count + 1):
            sink = self._discover_bluetooth_sink(mac)
            if sink is not None:
                self._logger.info("Sink discovered after %d attempt(s)", attempt)
                return sink

            if attempt < self._retry_count:
                self._logger.info(
                    "Bluetooth audio sink not ready; retrying in %.1f seconds",
                    self._retry_delay,
                )
                self._sleeper(self._retry_delay)

        self._logger.warning(
            "Sink not found after %d attempt(s)",
            self._retry_count,
        )
        return None

    def _discover_bluetooth_sink(self, device_mac: str) -> str | None:
        """Return the PulseAudio sink name belonging to *device_mac*, if any."""
        result = self._run_pactl("list", "short", "sinks")
        if result is None:
            return None

        device_identifier = device_mac.replace(":", "_").lower()
        for line in result.stdout.splitlines():
            fields = line.split(maxsplit=2)
            if len(fields) < 2:
                continue

            sink = fields[1]
            is_matching_bluetooth_sink = (
                sink.lower().startswith("bluez_output.")
                and device_identifier in sink.lower()
            )
            if is_matching_bluetooth_sink:
                self._logger.info("Found Bluetooth audio sink %s", sink)
                return sink

        return None

    def _set_default_sink(self, sink: str) -> bool:
        """Set *sink* as the server's default audio output."""
        self._logger.info("Setting Bluetooth sink %s as the default", sink)
        return self._run_pactl("set-default-sink", sink) is not None

    def _move_active_streams(self, sink: str) -> bool:
        """Move every active sink input to *sink*."""
        result = self._run_pactl("list", "short", "sink-inputs")
        if result is None:
            return False

        stream_ids = [
            fields[0]
            for line in result.stdout.splitlines()
            if (fields := line.split(maxsplit=1))
        ]
        self._logger.info(
            "Moving %d active audio stream(s) to %s",
            len(stream_ids),
            sink,
        )

        for stream_id in stream_ids:
            if self._run_pactl("move-sink-input", stream_id, sink) is None:
                self._logger.warning(
                    "Failed to move audio stream %s to %s",
                    stream_id,
                    sink,
                )
                return False

        return True

    def _run_pactl(self, *arguments: str) -> subprocess.CompletedProcess[str] | None:
        """Run ``pactl`` and convert command failures into a logged result."""
        command = ["pactl", *arguments]
        try:
            result = self._command_runner(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            self._logger.warning("Could not run %s: %s", " ".join(command), error)
            return None

        if result.returncode != 0:
            self._logger.warning(
                "Command failed (%d): %s; %s",
                result.returncode,
                " ".join(command),
                result.stderr.strip(),
            )
            return None

        return result

    def _notify_failure(self, message: str) -> None:
        self._logger.warning("Audio switching failed: %s", message)
        self._notify("Audio switching failed", message)

    def _notify(self, title: str, body: str) -> None:
        """Send a notification without allowing notification errors to stop BlueLink."""
        try:
            self._notifier.notify(title, body)
        except Exception:  # D-Bus notification services can disappear at runtime.
            self._logger.exception("Could not show audio-switching notification")
