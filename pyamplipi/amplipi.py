from typing import List, Optional, Dict, Any, Tuple

from aiohttp import ClientSession

from pyamplipi.client import Client
from pyamplipi.models import Group, Stream, SourceUpdate, MultiZoneUpdate, ZoneUpdate, \
    GroupUpdate, StreamUpdate, Announcement, Status, Config, Info, Source, Zone, Preset, \
    PresetUpdate, PlayMedia


json_ser_kwargs: Dict[str, Any] = dict(exclude_unset=True)

# play_media functionality added in 0.4.1
MIN_MEDIA_PLAYER_VERSION = (0, 4, 1)

class AmpliPi:
    def __init__(
            self,
            endpoint: str,
            timeout: int = 10,
            http_session: Optional[ClientSession] = None,
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
        self.version: Optional[Tuple[int]] = None

    # -- status calls
    async def get_status(self) -> Status:
        response = await self._client.get('')
        return Status.parse_obj(response)

    async def load_config(self, config: Config) -> Status:
        response = await self._client.post('load', config.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def factory_reset(self) -> Status:
        response = await self._client.post('factory_reset')
        return Status.parse_obj(response)

    async def system_reset(self) -> Status:
        response = await self._client.post('reset')
        return Status.parse_obj(response)

    async def system_reboot(self) -> Status:
        response = await self._client.post('reboot')
        return Status.parse_obj(response)

    async def system_shutdown(self) -> Status:
        response = await self._client.post('shutdown')
        return Status.parse_obj(response)

    async def get_info(self) -> Info:
        response = await self._client.get('info')
        return Info.parse_obj(response)

    # -- source calls
    async def get_sources(self) -> List[Source]:
        response = await self._client.get('sources')
        return [Source.parse_obj(source) for source in response['sources']]

    async def get_source(self, source_id: int) -> Source:
        response = await self._client.get(f'sources/{source_id}')
        return Source.parse_obj(response)

    async def set_source(self, source_id: int, source_update: SourceUpdate) -> Status:
        response = await self._client.patch(f'sources/{source_id}', source_update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def get_source_img(self, source_id: int, height: int, outfile: Optional[str] = None) -> None:
        await self._client.get(f'sources/{source_id}/image/{height}', expect_json=False, outfile=outfile)
        return None

    # -- zone calls
    async def get_zone(self, zone_id: int) -> Zone:
        response = await self._client.get(f'zones/{zone_id}')
        return Zone.parse_obj(response)

    async def get_zones(self) -> List[Zone]:
        response = await self._client.get('zones')
        return [Zone.parse_obj(zone) for zone in response['zones']]

    async def set_zones(self, zone_update: MultiZoneUpdate) -> Status:
        response = await self._client.patch('zones', zone_update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def set_zone(self, zone_id: int, zone_update: ZoneUpdate) -> Status:
        response = await self._client.patch(f'zones/{zone_id}',
                                            zone_update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    # -- group calls
    async def create_group(self, new_group: Group) -> Group:
        response = await self._client.post('group', new_group.json(**json_ser_kwargs))
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
        response = await self._client.patch(f'groups/{group_id}', update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    # -- stream calls
    async def get_streams(self) -> List[Stream]:
        response = await self._client.get('streams')
        return [Stream.parse_obj(stream) for stream in response['streams']]

    async def get_stream(self, stream_id: int) -> Stream:
        response = await self._client.get(f'streams/{stream_id}')
        return Stream.parse_obj(response)

    async def play_stream(self, stream_id: int) -> Status:
        response = await self._client.post(f'streams/{stream_id}/play')
        return Status.parse_obj(response)

    async def pause_stream(self, stream_id: int) -> Status:
        response = await self._client.post(f'streams/{stream_id}/pause')
        return Status.parse_obj(response)

    async def previous_stream(self, stream_id: int) -> Status:
        response = await self._client.post(f'streams/{stream_id}/prev')
        return Status.parse_obj(response)

    async def next_stream(self, stream_id: int) -> Status:
        response = await self._client.post(f'streams/{stream_id}/next')
        return Status.parse_obj(response)

    async def stop_stream(self, stream_id: int) -> Status:
        response = await self._client.post(f'streams/{stream_id}/stop')
        return Status.parse_obj(response)

    async def station_change_stream(self, stream_id: int, station: int) -> Status:
        response = await self._client.post(f'streams/{stream_id}/station={station}')
        return Status.parse_obj(response)

    async def create_stream(self, new_stream: Stream) -> Status:
        response = await self._client.post('stream', new_stream.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def delete_stream(self, stream_id: int) -> Status:
        response = await self._client.delete(f'streams/{stream_id}')
        return Status.parse_obj(response)

    async def set_stream(self, stream_id: int, update: StreamUpdate) -> Status:
        response = await self._client.post(f'streams/{stream_id}', update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    # -- preset calls
    async def get_presets(self) -> List[Preset]:
        response = await self._client.get('presets')
        return [Preset.parse_obj(preset) for preset in response['presets']]

    async def get_preset(self, preset_id: int) -> Preset:
        response = await self._client.get(f'presets/{preset_id}')
        return Preset.parse_obj(response)

    async def set_preset(self, preset_id: int, update: PresetUpdate) -> Status:
        response = await self._client.patch(f'presets/{preset_id}', update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def create_preset(self, new_preset: Preset) -> Preset:
        response = await self._client.post('preset', new_preset.json(**json_ser_kwargs))
        return Preset.parse_obj(response)

    async def delete_preset(self, preset_id: int) -> Status:
        response = await self._client.delete(f'presets/{preset_id}')
        return Status.parse_obj(response)

    async def load_preset(self, preset_id: int) -> Status:
        response = await self._client.post(f'presets/{preset_id}/load')
        return Status.parse_obj(response)

    # -- anounce call
    async def announce(self, announcement: Announcement) -> Status:
        response = await self._client.post('announce', announcement.json(**json_ser_kwargs))
        return Status.parse_obj(response)
    
    async def get_version(self):
        if self.version is not None:
            return self.version

        info = await self.get_info()
        version_raw = info.version
        version_nums = []
        tmp = 0
        for ch in version_raw:
            if ch.isdigit():
                tmp = (tmp*10) + int(ch)
            else:
                version_nums.append(tmp)
                tmp = 0
        version_nums.append(tmp)
        self.version = tuple(version_nums[:3])
        return self.version

    # -- play media call
    async def play_media(self, media: PlayMedia) -> Status:
        version = await self.get_version()
        if version < MIN_MEDIA_PLAYER_VERSION:  # TOO OLD, USE ANNOUNCEMENT
            announce = Announcement(media=media.media,
                                    source_id=media.source_id)
            response = await self._client.post('announce', announce.json(**json_ser_kwargs))
            return Status.parse_obj(response)
        else:
            response = await self._client.post('play', media.json(**json_ser_kwargs))
            return Status.parse_obj(response)

    # -- client control
    async def close(self):
        await self._client.close()
