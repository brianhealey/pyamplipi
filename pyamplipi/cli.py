# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio
import logging

from pyamplipi.amplipi import AmpliPi

_LOGGER = logging.getLogger(__name__)


async def get_status():
    amp = AmpliPi(
        "http://amplipi-dev.local:5000/api",
        10,
    )
    result = await amp.get_status()
    _LOGGER.info(result)
    await amp.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_status())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
