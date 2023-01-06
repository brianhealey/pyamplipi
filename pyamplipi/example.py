# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio
import logging

from pyamplipi.amplipi import AmpliPi
from pyamplipi.models import SourceUpdate

_LOGGER = logging.getLogger(__name__)


async def get_status():
    amp = AmpliPi(
        "http://amplipi-dev.local:5000/api",
        10,
    )
    result = await amp.get_status()
    source = result.sources.pop()
    stream = result.streams.pop()
    if source.id is not None and stream is not None and stream.id is not None:
        update = await amp.set_source(source.id, SourceUpdate(
            input=f'stream{stream.id}'
        ))
        _LOGGER.info(update)
    await amp.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_status())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
