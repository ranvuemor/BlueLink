# BlueLink

BlueLink is an event-driven Bluetooth auto-connect daemon for Linux.

It listens to BlueZ events over D-Bus and automatically reconnects trusted Bluetooth audio devices when they become available.

## Features

- Automatic Bluetooth headset reconnection
- Event-driven (no polling)
- Desktop notifications
- Journald logging
- Automatic audio switching after a successful Bluetooth connection
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
