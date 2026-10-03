from bluelink.audio import AudioManager
from bluelink.battery import BatteryMonitor
from bluelink.bluez import BlueZMonitor
from bluelink.config import Config
from bluelink.logger import get_logger
from bluelink.notifier import Notifier


def main():
    logger = get_logger()
    try:
        config = Config.from_file()
    except ValueError as error:
        logger.error("%s", error)
        return 2

    notifier = Notifier(logger)
    audio_manager = AudioManager(
        logger=logger,
        notifier=notifier,
        retry_count=config.audio_retry_count,
        retry_delay=config.audio_retry_delay,
    )
    battery_monitor = BatteryMonitor(
        logger=logger,
        notifier=notifier,
        enabled=config.battery_notifications,
    )

    monitor = BlueZMonitor(
        config=config,
        logger=logger,
        notifier=notifier,
        audio_manager=audio_manager,
        battery_monitor=battery_monitor,
    )

    monitor.run()
    return 0


if __name__ == "__main__":
    main()
