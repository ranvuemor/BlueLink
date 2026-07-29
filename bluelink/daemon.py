from bluelink.audio import AudioManager
from bluelink.bluez import BlueZMonitor
from bluelink.config import Config
from bluelink.logger import get_logger
from bluelink.notifier import Notifier


def main():
    config = Config(
        device_mac="98:A5:F9:25:83:9B",
    )

    logger = get_logger()

    notifier = Notifier()
    audio_manager = AudioManager(
        logger=logger,
        notifier=notifier,
        retry_count=config.audio_retry_count,
        retry_delay=config.audio_retry_delay,
    )

    monitor = BlueZMonitor(
        config=config,
        logger=logger,
        notifier=notifier,
        audio_manager=audio_manager,
    )

    monitor.run()


if __name__ == "__main__":
    main()
