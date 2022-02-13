import json
from typing import List

from aiohttp import ClientSession

from pyamplipi.client import Client
from pyamplipi.models import Group, Stream, SourceUpdate, MultiZoneUpdate, ZoneUpdate, \
    GroupUpdate, StreamUpdate, Announcement, Status, Source, Zone, Preset


class AmpliPi:
    def __init__(
            self,
            endpoint: str,
            timeout: 10,
            http_session: ClientSession = None,
            verify_ssl: bool = False,
            disable_insecure_warning: bool = True,
    ):
        self._client = Client(
            endpoint,
            timeout,
            http_session,
            verify_ssl,
            disable_insecure_warning,
        )

    async def get_status(self) -> Status:
        response = await self._client.get('')
        return Status.parse_obj(response)

    async def get_sources(self) -> List[Source]:
        response = await self._client.get('sources')
        return [Source.parse_obj(source) for source in response['sources']]

    async def get_source(self, source_id: int) -> Source:
        response = await self._client.get(f'sources/{source_id}')
        return Source.parse_obj(response)

    async def set_source(self, source_id: int, source_update: SourceUpdate) -> Status:
        response = await self._client.patch(f'sources/{source_id}', source_update.json())
        return Status.parse_obj(response)

    async def get_zone(self, zone_id: int) -> Zone:
        response = await self._client.get(f'zones/{zone_id}')
        return Zone.parse_obj(response)

    async def get_zones(self) -> List[Zone]:
        response = await self._client.get('zones')
        return [Zone.parse_obj(zone) for zone in response['zones']]

    async def set_zones(self, zone_update: MultiZoneUpdate) -> Status:
        response = await self._client.patch('zones', zone_update.json())
        return Status.parse_obj(response)

    async def set_zone(self, zone_id: int, zone_update: ZoneUpdate) -> Status:
        response = await self._client.patch(f'zones/{zone_id}',
                                            zone_update.json())
        return Status.parse_obj(response)

    async def create_group(self, new_group: Group) -> Group:
        response = await self._client.post('group', new_group.json())
        return Group.parse_obj(response)

    async def get_groups(self) -> List[Group]:
        response = await self._client.get('groups')
        return [Group.parse_obj(group) for group in response['groups']]

    async def get_group(self, group_id) -> Group:
        response = await self._client.get(f'groups/{group_id}')
        return Group.parse_obj(response)

    async def delete_group(self, group_id):
        response = await self._client.delete(f'groups/{group_id}')
        return Status.parse_obj(response)

    async def set_group(self, group_id, update: GroupUpdate) -> Status:
        response = await self._client.patch(f'groups/{group_id}', update.json())
        return Status.parse_obj(response)

    async def get_streams(self) -> List[Stream]:
        response = await self._client.get('streams')
        return [Stream.parse_obj(stream) for stream in response['streams']]

    async def get_stream(self, stream_id: int) -> Stream:
        response = await self._client.get(f'streams/{stream_id}')
        return Stream.parse_obj(response)

    async def play_stream(self, stream_id: int) -> Stream:
        response = await self._client.post(f'streams/{stream_id}/play')
        return Stream.parse_obj(response)

    async def pause_stream(self, stream_id: int) -> Stream:
        response = await self._client.post(f'streams/{stream_id}/pause')
        return Stream.parse_obj(response)

    async def previous_stream(self, stream_id: int) -> Stream:
        response = await self._client.post(f'streams/{stream_id}/prev')
        return Stream.parse_obj(response)

    async def next_stream(self, stream_id: int) -> Stream:
        response = await self._client.post(f'streams/{stream_id}/next')
        return Stream.parse_obj(response)

    async def create_stream(self, new_stream: Stream) -> Stream:
        response = await self._client.post(f'streams', new_stream.json())
        return Stream.parse_obj(response)

    async def delete_stream(self, stream_id: int) -> Status:
        response = await self._client.delete(f'streams/{stream_id}')
        return Status.parse_obj(response)

    async def set_stream(self, stream_id: int, update: StreamUpdate) -> Stream:
        response = await self._client.post(f'streams/{stream_id}', update.json())
        return Stream.parse_obj(response)

    async def announce(self, announcement: Announcement) -> Status:
        response = await self._client.post('announce', announcement.json())
        return Status.parse_obj(response)

    async def get_presets(self) -> List[Preset]:
        response = await self._client.get('presets')
        return [Preset.parse_obj(preset) for preset in response['presets']]

    async def close(self):
        await self._client.close()
