from bluelink.config import Config
from bluelink.logger import get_logger
from bluelink.notifier import Notifier
from bluelink.bluez import BlueZMonitor


def main():

    config = Config(
        device_mac="98:A5:F9:25:83:9B",
    )

    logger = get_logger()

    notifier = Notifier()

    monitor = BlueZMonitor(
        config=config,
        logger=logger,
        notifier=notifier,
    )

    monitor.run()


if __name__ == "__main__":
    main()