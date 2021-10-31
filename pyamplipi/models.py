"""AmpliPi Data Models - Extracted from the amplipi repo.
"""

from enum import Enum
from typing import List, Optional, Union


class SourceInfo:
    id: Optional[int]
    name: str
    state: str  # paused, playing, stopped, unknown, loading ???
    artist: Optional[str]
    track: Optional[str]
    album: Optional[str]
    station: Optional[str]  # name of radio station
    img_url: Optional[str]


class Source:
    """ An audio source """
    id: Optional[int]
    name: str
    input: str
    info: Optional[SourceInfo]  # Additional info about the current audio playing from the stream (generated during
    # playback')


class SourceUpdate:
    """ Partial reconfiguration of an audio Source """
    name: Optional[str]
    input: Optional[str]  # 'None', 'local', 'stream=ID'


class SourceUpdateWithId(SourceUpdate):
    """ Partial reconfiguration of a specific audio Source """
    id: int


class Zone:
    """ Audio output to a stereo pair of speakers, typically belonging to a room """
    id: Optional[int]
    name: str
    source_id: int
    mute: bool
    vol: int
    disabled: bool


class ZoneUpdate:
    """ Reconfiguration of a Zone """
    name: Optional[str]
    source_id: Optional[int]
    mute: Optional[bool]
    vol: Optional[int]
    disabled: Optional[bool]


class ZoneUpdateWithId(ZoneUpdate):
    """ Reconfiguration of a specific Zone """
    id: int


class MultiZoneUpdate:
    """ Reconfiguration of multiple zones specified by zone_ids and group_ids """
    id: Optional[int]
    name: str
    zones: Optional[List[int]]
    groups: Optional[List[int]]
    update: ZoneUpdate


class Group:
    """ A group of zones that can share the same audio input and be controlled as a group ie. Updstairs. Volume,
    mute, and source_id fields are aggregates of the member zones. """
    id: Optional[int]
    name: str
    source_id: Optional[int]
    zones: List[int]
    mute: Optional[bool]
    vol_delta: Optional[int]


class GroupUpdate:
    """ Reconfiguration of a Group """
    name: str
    source_id: Optional[int]
    zones: Optional[List[int]]
    mute: Optional[bool]
    vol_delta: Optional[int]


class GroupUpdateWithId(GroupUpdate):
    """ Reconfiguration of a specific Group """
    id: int


class Stream:
    """ Digital stream such as Pandora, Airplay or Spotify """
    id: Optional[int]
    name: str
    type: str
    user: Optional[str]
    password: Optional[str]
    station: Optional[str]
    url: Optional[str]
    logo: Optional[str]
    freq: Optional[str]
    client_id: Optional[str]
    token: Optional[str]


class StreamUpdate:
    """ Reconfiguration of a Stream """
    name: str
    user: Optional[str]
    password: Optional[str]
    station: Optional[str]
    url: Optional[str]
    logo: Optional[str]
    freq: Optional[str]


class StreamCommand(str, Enum):
    PLAY = 'play'
    PAUSE = 'pause'
    NEXT = 'next'
    PREV = 'prev'
    STOP = 'stop'
    LOVE = 'love'
    BAN = 'ban'
    SHELVE = 'shelve'


class PresetState:
    """ A set of partial configuration changes to make to sources, zones, and groups """
    id: Optional[int]
    name: str
    sources: Optional[List[SourceUpdateWithId]]
    zones: Optional[List[ZoneUpdateWithId]]
    groups: Optional[List[GroupUpdateWithId]]


class Command:
    """ A command to execute on a stream """
    id: Optional[int]
    name: str
    stream_id: int
    cmd: str


class Preset:
    """ A partial controller configuration the can be loaded on demand. In addition to most of the configuration
    found in Status, this can contain commands as well that configure the state of different streaming services. """
    id: Optional[int]
    name: str
    state: Optional[PresetState]
    commands: Optional[List[Command]]
    last_used: Union[int, None] = None


class PresetUpdate:
    """ Changes to a current preset

  The contents of state and commands will be completely replaced if populated. Merging old and new updates seems too
  complicated and error prone. """
    name: str
    state: Optional[PresetState]
    commands: Optional[List[Command]]


class Announcement:
    """ A PA-like Announcement
  IF no zones or groups are specified, all available zones are used
  """
    media: str
    vol: int
    source_id: int
    zones: Optional[List[int]]
    groups: Optional[List[int]]


class Info:
    """ Information about the settings used by the controller """
    config_file: str = 'Uknown'
    version: str = 'Unknown'
    mock_ctrl: bool = False
    mock_streams: bool = False


class Status:
    """ Full Controller Configuration and Status """
    sources: List[Source] = []
    zones: List[Zone] = []
    groups: List[Group] = []
    streams: List[Stream] = []
    presets: List[Preset] = []
    info: Optional[Info]
