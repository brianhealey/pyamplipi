import json
from typing import List

import requests as requests

from pyamplipi.client import Client
from pyamplipi.models import Group, Stream, SourceUpdate, MultiZoneUpdate, ZoneUpdate, \
    GroupUpdate, StreamUpdate, Announcement, Status, Source


class AmpliPi:
    def __init__(
            self,
            endpoint: str,
            timeout: 10,
            http_session: requests.Session = None,
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

    def get_source(self, source_id: int):
        return self._client.get(f'sources/{source_id}')

    def set_source(self, source_id: int, source_update: SourceUpdate):
        return self._client.patch(f'sources/{source_id}', json.dumps(source_update))

    def get_zones(self):
        return self._client.get('zones')

    def set_zones(self, zone_update: MultiZoneUpdate):
        return self._client.patch('zones', json.dumps(zone_update))

    def set_zone(self, zone_id: int, zone_update: ZoneUpdate):
        return self._client.patch(f'zones/{zone_id}', json.dumps(zone_update))

    def create_group(self, new_group: Group):
        return self._client.post('group', json.dumps(new_group))

    def get_groups(self):
        return self._client.get('groups')

    def get_group(self, group_id):
        return self._client.get(f'groups/{group_id}')

    def delete_group(self, group_id):
        return self._client.delete(f'groups/{group_id}')

    def set_group(self, group_id, update: GroupUpdate):
        return self._client.patch(f'groups/{group_id}', update.json())

    def get_streams(self):
        return self._client.get('streams')

    def get_stream(self, stream_id: int):
        return self._client.get(f'streams/{stream_id}')

    def create_stream(self, new_stream: Stream):
        return self._client.post(f'streams', json.dumps(new_stream))

    def delete_stream(self, stream_id: int):
        return self._client.delete(f'streams/{stream_id}')

    def set_stream(self, stream_id: int, update: StreamUpdate):
        return self._client.post(f'streams/{stream_id}', json.dumps(update))

    def announce(self, announcement: Announcement):
        return self._client.post('announce', json.dumps(announcement))

    def get_presets(self):
        return self._client.get('presets')
