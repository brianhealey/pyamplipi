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

    def get_status(self) -> Status:
        response = self._client.get('')
        return Status.parse_obj(response)

    def get_sources(self) -> List[Source]:
        response = self._client.get('sources')
        return [Source.parse_obj(source) for source in response['sources']]

    def get_source(self, source_id: int) -> Source:
        response = self._client.get(f'sources/{source_id}')
        return Source.parse_obj(response)

    def set_source(self, source_id: int, source_update: SourceUpdate) -> Source:
        response = self._client.patch(f'sources/{source_id}', json.dumps(source_update))
        return Source.parse_obj(response)

    def get_zones(self) -> List[Zone]:
        response = self._client.get('zones')
        return Zone.parse_obj(response)

    def set_zones(self, zone_update: MultiZoneUpdate) -> Status:
        response = self._client.patch('zones', json.dumps(zone_update))
        return Status.parse_obj(response)

    def set_zone(self, zone_id: int, zone_update: ZoneUpdate) -> Zone:
        response = self._client.patch(f'zones/{zone_id}', json.dumps(zone_update))
        return Zone.parse_obj(response)

    def create_group(self, new_group: Group) -> Group:
        response = self._client.post('group', json.dumps(new_group))
        return Group.parse_obj(response)

    def get_groups(self) -> List[Group]:
        response = self._client.get('groups')
        return [Group.parse_obj(group) for group in response]

    def get_group(self, group_id) -> Group:
        response = self._client.get(f'groups/{group_id}')
        return Group.parse_obj(response)

    def delete_group(self, group_id):
        response = self._client.delete(f'groups/{group_id}')
        return Status.parse_obj(response)

    def set_group(self, group_id, update: GroupUpdate) -> Group:
        response = self._client.patch(f'groups/{group_id}', update.json())
        return Group.parse_obj(response)

    def get_streams(self) -> Stream:
        response = self._client.get('streams')
        return Stream.parse_obj(response)

    def get_stream(self, stream_id: int) -> Stream:
        response = self._client.get(f'streams/{stream_id}')
        return Stream.parse_obj(response)

    def create_stream(self, new_stream: Stream) -> Stream:
        response = self._client.post(f'streams', json.dumps(new_stream))
        return Stream.parse_obj(response)

    def delete_stream(self, stream_id: int) -> Status:
        response = self._client.delete(f'streams/{stream_id}')
        return Status.parse_obj(response)

    def set_stream(self, stream_id: int, update: StreamUpdate) -> Stream:
        response = self._client.post(f'streams/{stream_id}', json.dumps(update))
        return Stream.parse_obj(response)

    def announce(self, announcement: Announcement) -> Status:
        response = self._client.post('announce', json.dumps(announcement))
        return Status.parse_obj(response)

    def get_presets(self) -> List[Preset]:
        response = self._client.get('presets')
        return [Preset.parse_obj(preset) for preset in response]
