"""A class for interacting with AmpliPi
"""

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
        """
        Initialize the AmpliPi client.

        Args:
            endpoint (str): The API endpoint for the AmpliPi system.
            timeout (int, optional): The timeout for HTTP requests. Defaults to 10 seconds.
            http_session (Optional[ClientSession], optional): An optional aiohttp ClientSession.
            verify_ssl (bool, optional): Whether to verify SSL certificates. Defaults to False.
            disable_insecure_warning (bool, optional): Whether to disable insecure request warnings. Defaults to True.
        """
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
        """
        Retrieve the current status of the AmpliPi system.

        Returns:
            Status: The current status of the system.
        """
        response = await self._client.get('')
        return Status.parse_obj(response)

    async def load_config(self, config: Config) -> Status:
        """
        Load a specified configuration into the AmpliPi system.

        Args:
            config (Config): The configuration to load.

        Returns:
            Status: The status of the load operation.
        """
        response = await self._client.post('load', config.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def factory_reset(self) -> Status:
        """
        Perform a factory reset of the AmpliPi system.

        Returns:
            Status: The status of the factory reset operation.
        """
        response = await self._client.post('factory_reset')
        return Status.parse_obj(response)

    async def system_reset(self) -> Status:
        """
        Reset the AmpliPi system.

        Returns:
            Status: The status of the system reset operation.
        """
        response = await self._client.post('reset')
        return Status.parse_obj(response)

    async def system_reboot(self) -> Status:
        """
        Reboot the AmpliPi system.

        Returns:
            Status: The status of the reboot operation.
        """
        response = await self._client.post('reboot')
        return Status.parse_obj(response)

    async def system_shutdown(self) -> Status:
        """
        Shut down the AmpliPi system.

        Returns:
            Status: The status of the shutdown operation.
        """
        response = await self._client.post('shutdown')
        return Status.parse_obj(response)

    async def get_info(self) -> Info:
        """
        Retrieve general information about the AmpliPi system.

        Returns:
            Info: Information about the system.
        """
        response = await self._client.get('info')
        return Info.parse_obj(response)

    async def get_version(self):
        """
        Get the current version of the AmpliPi system.

        Returns:
            Tuple[int]: A tuple representing the version number.
        """
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

    # -- source calls
    async def get_sources(self) -> List[Source]:
        """
        Retrieve a list of available audio sources.

        Returns:
            List[Source]: A list of available sources.
        """
        response = await self._client.get('sources')
        return [Source.parse_obj(source) for source in response['sources']]

    async def get_source(self, source_id: int) -> Source:
        """
        Retrieve details of a specific audio source.

        Args:
            source_id (int): The ID of the source to retrieve.

        Returns:
            Source: The details of the specified source.
        """
        response = await self._client.get(f'sources/{source_id}')
        return Source.parse_obj(response)

    async def set_source(self, source_id: int, source_update: SourceUpdate) -> Status:
        """
        Update details of a specific audio source.

        Args:
            source_id (int): The ID of the source to update.
            source_update (SourceUpdate): The update details for the source.

        Returns:
            Status: The status of the update operation.
        """
        response = await self._client.patch(f'sources/{source_id}', source_update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def get_source_img(self, source_id: int, height: int, outfile: Optional[str] = None) -> None:
        """
        Retrieve an image for a specific audio source.

        Args:
            source_id (int): The ID of the source.
            height (int): The desired height of the image.
            outfile (Optional[str], optional): Optional path to save the image.

        Returns:
            None
        """
        await self._client.get(f'sources/{source_id}/image/{height}', expect_json=False, outfile=outfile)
        return None

    # -- zone calls
    async def get_zone(self, zone_id: int) -> Zone:
        """
        Retrieve details of a specific zone.

        Args:
            zone_id (int): The ID of the zone to retrieve.

        Returns:
            Zone: The details of the specified zone.
        """
        response = await self._client.get(f'zones/{zone_id}')
        return Zone.parse_obj(response)

    async def get_zones(self) -> List[Zone]:
        """
        Retrieve a list of available zones.

        Returns:
            List[Zone]: A list of available zones.
        """
        response = await self._client.get('zones')
        return [Zone.parse_obj(zone) for zone in response['zones']]

    async def set_zones(self, zone_update: MultiZoneUpdate) -> Status:
        """
        Update details of multiple zones.

        Args:
            zone_update (MultiZoneUpdate): The update details for the zones.

        Returns:
            Status: The status of the update operation.
        """
        response = await self._client.patch('zones', zone_update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def set_zone(self, zone_id: int, zone_update: ZoneUpdate) -> Status:
        """
        Update details of a specific zone.

        Args:
            zone_id (int): The ID of the zone to update.
            zone_update (ZoneUpdate): The update details for the zone.

        Returns:
            Status: The status of the update operation.
        """
        response = await self._client.patch(f'zones/{zone_id}',
                                            zone_update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    # -- group calls
    async def create_group(self, new_group: Group) -> Group:
        """
        Create a new group.

        Args:
            new_group (Group): The details of the new group.

        Returns:
            Group: The created group.
        """
        response = await self._client.post('group', new_group.json(**json_ser_kwargs))
        return Group.parse_obj(response)

    async def get_groups(self) -> List[Group]:
        """
        Retrieve a list of available groups.

        Returns:
            List[Group]: A list of available groups.
        """
        response = await self._client.get('groups')
        return [Group.parse_obj(group) for group in response['groups']]

    async def get_group(self, group_id) -> Group:
        """
        Retrieve details of a specific group.

        Args:
            group_id: The ID of the group to retrieve.

        Returns:
            Group: The details of the specified group.
        """
        response = await self._client.get(f'groups/{group_id}')
        return Group.parse_obj(response)

    async def delete_group(self, group_id):
        """
        Delete a specific group.

        Args:
            group_id: The ID of the group to delete.

        Returns:
            Status: The status of the delete operation.
        """
        response = await self._client.delete(f'groups/{group_id}')
        return Status.parse_obj(response)

    async def set_group(self, group_id, update: GroupUpdate) -> Status:
        """
        Update details of a specific group.

        Args:
            group_id: The ID of the group to update.
            update (GroupUpdate): The update details for the group.

        Returns:
            Status: The status of the update operation.
        """
        response = await self._client.patch(f'groups/{group_id}', update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    # -- stream calls
    async def get_streams(self) -> List[Stream]:
        """
        Retrieve a list of available streams.

        Returns:
            List[Stream]: A list of available streams.
        """
        response = await self._client.get('streams')
        return [Stream.parse_obj(stream) for stream in response['streams']]

    async def get_stream(self, stream_id: int) -> Stream:
        """
        Retrieve details of a specific stream.

        Args:
            stream_id (int): The ID of the stream to retrieve.

        Returns:
            Stream: The details of the specified stream.
        """
        response = await self._client.get(f'streams/{stream_id}')
        return Stream.parse_obj(response)

    async def play_stream(self, stream_id: int) -> Status:
        """
        Play a specific stream.

        Args:
            stream_id (int): The ID of the stream to play.

        Returns:
            Status: The status of the play operation.
        """
        response = await self._client.post(f'streams/{stream_id}/play')
        return Status.parse_obj(response)

    async def pause_stream(self, stream_id: int) -> Status:
        """
        Pause a specific stream.

        Args:
            stream_id (int): The ID of the stream to pause.

        Returns:
            Status: The status of the pause operation.
        """
        response = await self._client.post(f'streams/{stream_id}/pause')
        return Status.parse_obj(response)

    async def previous_stream(self, stream_id: int) -> Status:
        """
        Play the previous stream.

        Args:
            stream_id (int): The ID of the current stream.

        Returns:
            Status: The status of the previous stream operation.
        """
        response = await self._client.post(f'streams/{stream_id}/prev')
        return Status.parse_obj(response)

    async def next_stream(self, stream_id: int) -> Status:
        """
        Play the next stream.

        Args:
            stream_id (int): The ID of the current stream.

        Returns:
            Status: The status of the next stream operation.
        """
        response = await self._client.post(f'streams/{stream_id}/next')
        return Status.parse_obj(response)

    async def stop_stream(self, stream_id: int) -> Status:
        """
        Stop a specific stream.

        Args:
            stream_id (int): The ID of the stream to stop.

        Returns:
            Status: The status of the stop operation.
        """
        response = await self._client.post(f'streams/{stream_id}/stop')
        return Status.parse_obj(response)

    async def station_change_stream(self, stream_id: int, station: int) -> Status:
        """
        Change the station of a specific stream.

        Args:
            stream_id (int): The ID of the stream to change.
            station (int): The new station ID.

        Returns:
            Status: The status of the station change operation.
        """
        response = await self._client.post(f'streams/{stream_id}/station={station}')
        return Status.parse_obj(response)

    async def create_stream(self, new_stream: Stream) -> Status:
        """
        Create a new stream.

        Args:
            new_stream (Stream): The details of the new stream.

        Returns:
            Status: The status of the create operation.
        """
        response = await self._client.post('stream', new_stream.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def delete_stream(self, stream_id: int) -> Status:
        """
        Delete a specific stream.

        Args:
            stream_id (int): The ID of the stream to delete.

        Returns:
            Status: The status of the delete operation.
        """
        response = await self._client.delete(f'streams/{stream_id}')
        return Status.parse_obj(response)

    async def set_stream(self, stream_id: int, update: StreamUpdate) -> Status:
        """
        Update details of a specific stream.

        Args:
            stream_id (int): The ID of the stream to update.
            update (StreamUpdate): The update details for the stream.

        Returns:
            Status: The status of the update operation.
        """
        response = await self._client.post(f'streams/{stream_id}', update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    # -- preset calls
    async def get_presets(self) -> List[Preset]:
        """
        Retrieve a list of available presets.

        Returns:
            List[Preset]: A list of available presets.
        """
        response = await self._client.get('presets')
        return [Preset.parse_obj(preset) for preset in response['presets']]

    async def get_preset(self, preset_id: int) -> Preset:
        """
        Retrieve details of a specific preset.

        Args:
            preset_id (int): The ID of the preset to retrieve.

        Returns:
            Preset: The details of the specified preset.
        """
        response = await self._client.get(f'presets/{preset_id}')
        return Preset.parse_obj(response)

    async def set_preset(self, preset_id: int, update: PresetUpdate) -> Status:
        """
        Update details of a specific preset.

        Args:
            preset_id (int): The ID of the preset to update.
            update (PresetUpdate): The update details for the preset.

        Returns:
            Status: The status of the update operation.
        """
        response = await self._client.patch(f'presets/{preset_id}', update.json(**json_ser_kwargs))
        return Status.parse_obj(response)

    async def create_preset(self, new_preset: Preset) -> Preset:
        """
        Create a new preset.

        Args:
            new_preset (Preset): The details of the new preset.

        Returns:
            Preset: The created preset.
        """
        response = await self._client.post('preset', new_preset.json(**json_ser_kwargs))
        return Preset.parse_obj(response)

    async def delete_preset(self, preset_id: int) -> Status:
        """
        Delete a specific preset.

        Args:
            preset_id (int): The ID of the preset to delete.

        Returns:
            Status: The status of the delete operation.
        """
        response = await self._client.delete(f'presets/{preset_id}')
        return Status.parse_obj(response)

    async def load_preset(self, preset_id: int) -> Status:
        """
        Load a specific preset.

        Args:
            preset_id (int): The ID of the preset to load.

        Returns:
            Status: The status of the load operation.
        """
        response = await self._client.post(f'presets/{preset_id}/load')
        return Status.parse_obj(response)

    # -- anounce call
    async def announce(self, announcement: Announcement, timeout: int = None) -> Status:
        """
        Announce a message using the AmpliPi system.

        Args:
            announcement (Announcement): The announcement details.
            timeout (int, optional): Optional timeout for the announcement.

        Returns:
            Status: The status of the announcement operation.
        """
        response = await self._client.post('announce', announcement.json(**json_ser_kwargs), timeout=timeout)
        return Status.parse_obj(response)

    # -- play media call
    async def play_media(self, media: PlayMedia) -> Status:
        """
        Play a specific media file.

        Args:
            media (PlayMedia): The media details to play.

        Returns:
            Status: The status of the play operation.
        """
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
        """
        Close the AmpliPi client session.

        Returns:
            None
        """
        await self._client.close()

