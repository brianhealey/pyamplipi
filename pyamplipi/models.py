"""AmpliPi Data Models - Extracted from the amplipi repo.
"""

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel


class SourceInfo(BaseModel):
    """ Info about the current audio playing from the connected stream (generated during playback) """
    name: str
    state: str  # paused, playing, stopped, unknown, loading ???
    artist: Optional[str] = None
    track: Optional[str] = None
    album: Optional[str] = None
    station: Optional[str] = None  # name of radio station
    img_url: Optional[str] = None
    supported_cmds: List[str] = []


class Source(BaseModel):
    """ An audio source """
    id: Optional[int] = None
    name: str
    input: str
    # Additional info about the current audio playing from the stream (generated during
    info: Optional[SourceInfo] = None
    # playback')


class SourceUpdate(BaseModel):
    """ Partial reconfiguration of an audio Source """
    name: Optional[str] = None
    input: Optional[str] = None  # 'None', 'local', 'stream=ID'


class SourceUpdateWithId(SourceUpdate):
    """ Partial reconfiguration of a specific audio Source """
    id: int


class Zone(BaseModel):
    """ Audio output to a stereo pair of speakers, typically belonging to a room """
    id: Optional[int] = None
    name: str
    source_id: int
    mute: bool
    vol: int
    vol_f: float
    vol_min: int
    vol_max: int
    disabled: bool


class ZoneUpdate(BaseModel):
    """ Reconfiguration of a Zone """
    name: Optional[str] = None
    source_id: Optional[int] = None
    mute: Optional[bool] = None
    vol: Optional[int] = None
    vol_f: Optional[float] = None
    vol_min: Optional[int] = None
    vol_max: Optional[int] = None
    disabled: Optional[bool] = None


class ZoneUpdateWithId(ZoneUpdate):
    """ Reconfiguration of a specific Zone """
    id: int


class MultiZoneUpdate(BaseModel):
    """ Reconfiguration of multiple zones specified by zone_ids and group_ids """
    zones: Optional[List[int]] = None
    groups: Optional[List[int]] = None
    update: ZoneUpdate


class Group(BaseModel):
    """ A group of zones that can share the same audio input and be controlled as a group ie. Upstairs. Volume, mute,
    and source_id fields are aggregates of the member zones."""
    id: Optional[int] = None
    name: str
    source_id: Optional[int] = None
    zones: List[int]
    mute: Optional[bool] = None
    vol_delta: Optional[int] = None
    vol_f: Optional[float] = None


class GroupUpdate(BaseModel):
    """ Reconfiguration of a Group """
    name: Optional[str] = None
    source_id: Optional[int] = None
    zones: Optional[List[int]] = None
    mute: Optional[bool] = None
    vol_delta: Optional[int] = None
    vol_f: Optional[float] = None


class GroupUpdateWithId(GroupUpdate):
    """ Reconfiguration of a specific Group """
    id: int


class Stream(BaseModel):
    """ Digital stream such as Pandora, AirPlay or Spotify """
    id: Optional[int] = None
    name: str
    type: str
    user: Optional[str] = None
    password: Optional[str] = None
    station: Optional[str] = None
    url: Optional[str] = None
    logo: Optional[str] = None
    freq: Optional[str] = None
    client_id: Optional[str] = None
    token: Optional[str] = None


class StreamUpdate(BaseModel):
    """ Reconfiguration of a Stream """
    name: str
    user: Optional[str] = None
    password: Optional[str] = None
    station: Optional[str] = None
    url: Optional[str] = None
    logo: Optional[str] = None
    freq: Optional[str] = None


class StreamCommand(str, Enum):
    PLAY = 'play'
    PAUSE = 'pause'
    NEXT = 'next'
    PREV = 'prev'
    STOP = 'stop'
    LOVE = 'love'
    BAN = 'ban'
    SHELVE = 'shelve'


class PresetState(BaseModel):
    """ A set of partial configuration changes to make to sources, zones, and groups """
    sources: Optional[List[SourceUpdateWithId]] = None
    zones: Optional[List[ZoneUpdateWithId]] = None
    groups: Optional[List[GroupUpdateWithId]] = None


class Command(BaseModel):
    """ A command to execute on a stream """
    stream_id: int
    cmd: str


class Preset(BaseModel):
    id: Optional[int] = None
    name: str
    state: Optional[PresetState] = None
    commands: Optional[List[Command]] = None
    last_used: Union[int, None] = None


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[PresetState] = None
    commands: Optional[List[Command]] = None


class Announcement(BaseModel):
    media: str
    vol: Optional[int] = None
    vol_f: Optional[float] = None
    source_id: Optional[int] = None
    zones: Optional[List[int]] = None
    groups: Optional[List[int]] = None


class PlayMedia(BaseModel):
    media: str
    vol: Optional[int] = None
    vol_f: Optional[float] = None
    source_id: Optional[int] = None


class FirmwareInfo(BaseModel):
    version: Optional[str] = None
    git_hash: Optional[str] = None
    git_dirty: Optional[bool] = None


class Info(BaseModel):
    config_file: str = 'Uknown'
    version: str = 'Unknown'
    mock_ctrl: bool = False
    mock_streams: bool = False
    online: Optional[bool] = True
    latest_release: Optional[str] = None
    fw: Optional[List[FirmwareInfo]] = None


class Config(BaseModel):
    sources: List[Source] = []
    zones: List[Zone] = []
    groups: List[Group] = []
    streams: List[Stream] = []
    presets: List[Preset] = []


class Status(Config):
    info: Optional[Info] = None


class AppSettings(BaseModel):
    mock_ctrl: bool = True
    mock_streams: bool = True
    config_file: str = 'house.json'
    delay_saves: bool = True
