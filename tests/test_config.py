import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bluelink.config import Config


class ConfigTests(unittest.TestCase):
    def write_config(self, contents: str) -> Path:
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "config.toml"
        path.write_text(contents)
        return path

    def test_loads_config_and_uses_defaults(self) -> None:
        config = Config.from_file(self.write_config('device_mac = "AA:BB:CC:DD:EE:FF"'))

        self.assertEqual(config.device_mac, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(config.audio_retry_count, 10)
        self.assertTrue(config.battery_notifications)

    def test_rejects_unknown_options(self) -> None:
        path = self.write_config(
            'device_mac = "AA:BB:CC:DD:EE:FF"\nnotifcations = true'
        )

        with self.assertRaisesRegex(ValueError, "notifcations"):
            Config.from_file(path)

    def test_rejects_invalid_retry_count(self) -> None:
        path = self.write_config(
            'device_mac = "AA:BB:CC:DD:EE:FF"\naudio_retry_count = 0'
        )

        with self.assertRaisesRegex(ValueError, "audio_retry_count"):
            Config.from_file(path)


if __name__ == "__main__":
    unittest.main()
