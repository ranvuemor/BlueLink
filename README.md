# BlueLink

BlueLink is an event-driven Bluetooth auto-connect daemon for Linux.

It listens to BlueZ events over D-Bus and automatically reconnects trusted Bluetooth audio devices when they become available.

## Features

- Automatic Bluetooth headset reconnection
- Event-driven (no polling)
- Desktop notifications
- Journald logging
- Automatic audio switching after a successful Bluetooth connection
- Audio-sink discovery retries while PipeWire starts
- AirPods battery support (planned)
- Works with BlueZ and PipeWire

## Roadmap

- [x] Auto reconnect
- [ ] Notifications
- [ ] Journald logging
- [ ] D-Bus Connect()
- [ ] Config file
- [x] Audio switching
- [ ] Battery support
- [ ] GTK4 frontend

## Audio switching retries

BlueZ can report a connected headset before PipeWire or PulseAudio exposes its
`bluez_output.*` sink. BlueLink checks for that sink up to 10 times, waiting
0.5 seconds between checks. Configure these values with `audio_retry_count` and
`audio_retry_delay` on `Config`.
