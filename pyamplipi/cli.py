# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio
import logging

from pyamplipi.amplipi import AmpliPi
from pyamplipi.models import ZoneUpdate, ZoneUpdateWithId

_LOGGER = logging.getLogger(__name__)


async def get_status():
    amp = AmpliPi(
        "http://amplipi-dev.local:5000/api",
        10,
    )
    result = await amp.get_status()
    zone = result.zones.pop()
    update = await amp.set_zone(zone.id, ZoneUpdate(
        name=zone.name,
        source_id=zone.source_id,
        mute=not zone.mute,
        vol=zone.vol - 5,
        disabled=not zone.disabled
    ))
    _LOGGER.info(update)
    await amp.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_status())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
