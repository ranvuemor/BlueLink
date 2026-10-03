# BlueLink

BlueLink is an event-driven Bluetooth auto-connect daemon for Linux.

It listens to BlueZ events over D-Bus and automatically reconnects a configured
Bluetooth audio device when it becomes available. It can route current audio to
the device through PipeWire/PulseAudio and report its battery level when BlueZ
provides one.

## Features

- Automatic Bluetooth headset reconnection through BlueZ `Device1.Connect()`
- Event-driven (no polling)
- Desktop notifications, with a safe fallback when no notification service runs
- Systemd/journald-compatible logging
- Automatic audio switching after a successful Bluetooth connection
- Audio-sink discovery retries while PipeWire starts
- Bluetooth battery notifications via BlueZ `Battery1`
- Works with BlueZ and PipeWire

## Roadmap

- [x] Auto reconnect
- [x] Notifications
- [x] Journald logging
- [x] D-Bus Connect()
- [x] Config file
- [x] Audio switching
- [x] Battery support
- [x] GTK4 frontend

## Configuration

Create `~/.config/bluelink/config.toml` with the Bluetooth device you want
BlueLink to manage:

```toml
device_mac = "98:A5:F9:25:83:9B"

# Optional values shown with their defaults.
reconnect_delay_ms = 1000
cooldown_seconds = 5
audio_retry_count = 10
audio_retry_delay = 0.5
notifications = true
battery_notifications = true
```

BlueLink refuses missing, invalid, or misspelled configuration so it does not
quietly connect the wrong device. Run it with `bluelink` after installing the
package. Under a systemd user service, inspect its logs with:

```bash
journalctl --user -u bluelink -f
```

For contributors with the development tools on `PATH`, run `make test`,
`make lint`, and `make format`.

## GTK4 frontend

Run `bluelink-gui` to open a small status window for the configured device. It
shows whether BlueZ sees the device as connected, can request a connection,
and refreshes the state on demand. The GUI uses the same configuration file as
the daemon and requires the GTK4 typelib supplied by your Linux distribution.

## Battery support

When BlueZ exposes `org.bluez.Battery1` (or a device `BatteryPercentage`),
BlueLink logs the percentage and sends a desktop notification when it changes.
Battery reporting depends on the headset and BlueZ version; it does not affect
reconnection or audio switching when unavailable.

## Audio switching retries

BlueZ can report a connected headset before PipeWire or PulseAudio exposes its
`bluez_output.*` sink. BlueLink checks for that sink up to 10 times, waiting
0.5 seconds between checks. Configure these values with `audio_retry_count` and
`audio_retry_delay` on `Config`.
