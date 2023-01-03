import logging
import logging.config
import asyncio
import sys
import os
import json
import yaml
import datetime
from dotenv import load_dotenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, Action, ArgumentError
from typing import Optional, List, Callable, Sequence, Dict, Any
from pydantic import BaseModel
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from aiohttp import TCPConnector, ClientSession
from aiohttp.client_exceptions import ServerDisconnectedError
from tabulate import tabulate
from textwrap import indent
import validators
from .models import Status, Config, Info, Source, Zone, Group, Stream, Preset, Announcement, \
    SourceUpdate, ZoneUpdate, MultiZoneUpdate, GroupUpdate, StreamUpdate, PresetUpdate
from .amplipi import AmpliPi
from .error import APIError


# constants
log = logging.getLogger(__name__)                     # central logging channel
json_ser_kwargs: Dict[str, Any] = dict(exclude_unset=True, indent=2)  # arguments to serialise the json


# text formatters
def em(msg: str) -> str: return f'\033[4m{msg}\033[0m'                                   # underline text for emphasis
def table(d, h) -> str: return indent(tabulate(d, h, tablefmt='rounded_outline'), '  ')  # make a nice indented table


def model_list_to_json(it: Sequence[BaseModel]) -> str:     # simple list json for List[BaseModel] constructs
    return f"[{','.join([i.json(**json_ser_kwargs) for i in it])}]"


# list methods dumping comprehensive output to stdout
def list_info(info: Info):
    print(em("Info:"))
    headers = ["Filename", "Version", "Mock Controls", "Mock Streams", "Online", "Firmware(s)"]
    data = list()
    data.append([
        info.config_file, info.version,
        info.mock_ctrl, info.mock_streams, info.online,
        "/".join([f"{fw.version}{'*' if fw.git_dirty else ''}" for fw in info.fw]) if info.fw else None,
    ])
    print(table(data, headers))


def list_sources(sources: List[Source]):
    print(em(f"Sources[{len(sources)}]"))
    headers = ["ID", "Name", "Input", "Info", "State"]
    data = [[s.id, s.name, s.input, s.info.name if s.info else None, s.info.state if s.info else None] for s in sources]
    print(table(data, headers))


def list_zones(zones: List[Zone]):
    print(em(f"Zones[{len(zones)}]"))
    headers = ["ID", "Name", "Volume (dB)", "Volume%", "Range (dB)", "Muted"]
    data = [[z.id, z.name, z.vol, z.vol_f, f"{z.vol_min}..{z.vol_max}", z.mute] for z in zones]
    print(table(data, headers))


def list_groups(groups: List[Group]):
    print(em(f"Groups[{len(groups)}]"))
    headers = ["ID", "Name", "Zones"]
    data = [[g.id, g.name, ','.join([str(z) for z in g.zones])] for g in groups]
    print(table(data, headers))


def list_streams(streams: List[Stream]):
    print(em(f"Streams[{len(streams)}]"))
    headers = ["ID", "Name", "Type"]
    data = [[s.id, s.name, s.type] for s in streams]
    print(table(data, headers))


def list_presets(presets: List[Preset]):
    print(em(f"Presets[{len(presets)}]"))
    headers = ["ID", "Name", "Last Used At"]
    data = [[p.id, p.name, datetime.datetime.fromtimestamp(p.last_used) if p.last_used is not None else None] for p in presets]
    print(table(data, headers))


def list_status(status: Status):
    if status.info:
        list_info(status.info)
    list_sources(status.sources)
    list_zones(status.zones)
    list_groups(status.groups)
    list_streams(status.streams)
    list_presets(status.presets)


# interactive confirm
def interactive_confirm(msg: str = 'This is not without danger.'):
    """ Asks interactively if the user really wants to proceed.
    """
    # reopen the tty to make sure the stdin read() until EOF has not closed it
    sys.stdin = open("/dev/tty")  # TODO check how this behaves on windows?
    answer = input(f'{em("Caution:")} {msg}. Are you sure [N/y]?').lower()
    return len(answer) > 0 and answer[0] == 'y'


# helper io functions
def read_in(infile: Optional[str] = None) -> str:
    """ Read input from infile (if not None) else from stdin
    """
    json_str: Optional[str] = None
    if infile is None:
        json_str = sys.stdin.read()
    else:
        with open(infile, 'r') as ins:
            json_str = ins.read()
    return json_str


def write_out(json_str: str, outfile: Optional[str] = None):
    """ Write output to outfile (if not None) els to stdout
    """
    if outfile is None:
        print(json_str)
    else:
        with open(outfile, 'w') as out:
            out.write(json_str)


# actual service-methods
# -- status section
async def do_placeholder(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ placeholder function during dev - to be removed when completed
    """
    log.warning(f"todo handle command args --> \n  args = {args}\n  ammplipi = {amplipi}")


async def do_status_list(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Prints out comprehensive status information
    """
    log.debug("status.list")
    status: Status = await amplipi.get_status()
    list_status(status)


async def do_status_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Status json represenatation
    """
    log.debug("status.get()")
    status: Status = await amplipi.get_status()
    write_out(status.json(**json_ser_kwargs), args.outfile)


async def do_config_load(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Sets Config json represenatation
    """
    log.debug(f"config.load(«stdin») forced = {args.force}")
    # Be sure to consume stdin before entering interactive dialogue
    new_config: Config = instantiate_model(Config, args.infile)  # not using any --input and no validate()
    # Make sure the user wants this
    assert args.force or interactive_confirm("You are about to overwrite the configuration."), \
        "Lacking end-user confirmation. Aborted!"
    await amplipi.load_config(new_config)  # ignoring status return value


async def do_factory_reset(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Performs factory reset
    """
    log.debug(f"config.factory_reset() forced = {args.force}")
    # Make sure the user wants this
    assert args.force or interactive_confirm("You are about to reset the configuration to factory defaults."), \
        "Lacking end-user confirmation. Aborted!"
    await amplipi.factory_reset()  # ignoring status return value


async def do_system_reset(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Reload the current configuration, resetting the firmware in the process.
    """
    log.debug(f"system.reset() forced = {args.force}")
    # Make sure the user wants this
    assert args.force or interactive_confirm("You are about to reset the system firmware and reload the current config."), \
        "Lacking end-user confirmation. Aborted!"
    await amplipi.system_reset()  # ignoring status return value


async def do_system_reboot(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Restart the OS and all of the AmpliPi services.
    """
    log.debug(f"system.reboot() forced = {args.force}")
    # Make sure the user wants this
    assert args.force or interactive_confirm("You are about to reboot the system OS and all running services."), \
        "Lacking end-user confirmation. Aborted!"
    await amplipi.system_reboot()  # ignoring status return value


async def do_system_shutdown(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Clean shutdown of AmpliPi and its OS.
    """
    log.debug(f"system.shutdown() forced = {args.force}")
    # Make sure the user wants this
    assert args.force or interactive_confirm("You are about to shutdown the system OS."), \
        "Lacking end-user confirmation. Aborted!"
    await amplipi.system_shutdown()  # ignoring status return value


async def do_info_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Status-Info json represenatation
    """
    log.debug("status.info()")
    info: Info = await amplipi.get_info()
    write_out(info.json(**json_ser_kwargs), args.outfile)


# -- source section
async def do_source_list(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Prints out comprehensive listing of sources
    """
    log.debug("source.list")
    sources: List[Source] = await amplipi.get_sources()
    list_sources(sources)


async def do_source_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Source(id) json represenatation by source_id
    """
    log.debug(f"source.get({args.sourceid})")
    assert 0 <= args.sourceid <= 3, "source id must be in range 0..3"
    source: Source = await amplipi.get_source(args.sourceid)
    write_out(source.json(**json_ser_kwargs), args.outfile)


async def do_source_getall(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Sources json represenatation
    """
    log.debug("source.getall()")
    sources: List[Source] = await amplipi.get_sources()
    write_out(model_list_to_json(sources), args.outfile)


async def do_source_set(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Update a source(id)'s configuration
    """
    log.debug(f"source.set({args.sourceid}, input={args.input if args.input is not None else '«stdin»'})")
    assert 0 <= args.sourceid <= 3, "source id must be in range 0..3"

    def validate(input: dict):
        log.debug(f"validating source_update kwargs: {input}")
        assert any(input.values()), "no actual source values to be set"
    src_update: SourceUpdate = instantiate_model(SourceUpdate, args.infile, args.input, validate)
    await amplipi.set_source(args.sourceid, src_update)  # ignoring status return value


async def do_source_getimg(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Get a square jpeg image representing the current media playing on source(id)
    """
    log.debug(f"source.getimg({args.sourceid}, {args.size})")
    assert 0 <= args.sourceid <= 3, "source id must be in range 0..3"
    assert 1 <= args.size <= 500, "image size must be in range 1..500"
    assert args.outfile, "Please provide a -O outfile because the jpeg output will clutter stdout/terminal"
    await amplipi.get_source_img(args.sourceid, args.size, args.outfile)


# -- zone section
async def do_zone_list(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Prints out comprehensive listing of zones
    """
    log.debug("zone.list")
    zones: List[Zone] = await amplipi.get_zones()
    list_zones(zones)


async def do_zone_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Zone json represenatation by zone_id
    """
    log.debug(f"zone.get({args.zoneid})")
    assert 0 <= args.zoneid <= 35, "zone id must be in range 0..35"
    zone: Zone = await amplipi.get_zone(args.zoneid)
    write_out(zone.json(**json_ser_kwargs), args.outfile)


async def do_zone_getall(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Zones json represenatation
    """
    log.debug("zone.getall()")
    zones: List[Zone] = await amplipi.get_zones()
    write_out(model_list_to_json(zones), args.outfile)


async def do_zone_set(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Update a zone(id)'s configuration
    """
    log.debug(f"zone.set({args.zoneid}, input={args.input if args.input is not None else '«stdin»'})")
    assert 0 <= args.zoneid <= 35, "zone id must be in range 0..35"

    def validate(input: dict):
        log.debug(f"validating zone_update kwargs: {input}")
        assert len(input.keys()) > 0, "no actual zone values to be set"
    zone_update: ZoneUpdate = instantiate_model(ZoneUpdate, args.infile, args.input, validate)
    await amplipi.set_zone(args.zoneid, zone_update)  # ignoring status return value


async def do_zone_setall(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Update a bunch of zones (and groups) with the same configuration changes
    """
    log.debug("zone.setall(«stdin»)")
    mzone_update: MultiZoneUpdate = instantiate_model(MultiZoneUpdate, args.infile)  # not supporting -i
    await amplipi.set_zones(mzone_update)  # ignoring status return value


# -- group section
async def do_group_list(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Prints out comprehensive listing of groups
    """
    log.debug("group.list")
    groups: List[Group] = await amplipi.get_groups()
    list_groups(groups)


async def do_group_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Group json represenatation by group_id
    """
    log.debug(f"group.get({args.groupid})")
    assert 0 <= args.groupid, "group id must be > 0"
    group: Group = await amplipi.get_group(args.groupid)
    write_out(group.json(**json_ser_kwargs), args.outfile)


async def do_group_getall(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Groups json represenatation
    """
    log.debug("group.getall()")
    groups: List[Group] = await amplipi.get_groups()
    write_out(model_list_to_json(groups), args.outfile)


async def do_group_set(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Update a group(id)'s configuration
    """
    log.debug(f"group.set({args.groupid}, input={args.input if args.input is not None else '«stdin»'})")
    assert 0 <= args.groupid, "group id must be > 0"

    def validate(input: dict):
        log.debug(f"validating group_update kwargs: {input}")
        assert len(input.keys()) > 0, "no actual group values to be set"
    group_update: GroupUpdate = instantiate_model(GroupUpdate, args.infile, args.input, validate)
    await amplipi.set_group(args.groupid, group_update)  # ignoring status return value


async def do_group_new(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Create a new grouping of zones
    """
    log.debug(f"group.create(input={args.input if args.input is not None else '«stdin»'})")

    def validate(input: dict):
        log.debug(f"validating group_update kwargs: {input}")
        assert all((input.get('name'), input.get('zones'))), "group needs a name and list of zones"
        assert all([bool(0 <= zid <= 35) for zid in input['zones']]), "zone ids must be in range 0..35"
    group: Group = instantiate_model(Group, args.infile, args.input, validate)
    await amplipi.create_group(group)  # ignoring status return value


async def do_group_del(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Delete the group by groupid
    """
    log.debug(f"group.delete({args.groupid})")
    assert 0 <= args.groupid, "group id must be > 0"
    await amplipi.delete_group(args.groupid)  # ignoring status return value


# -- stream section
async def do_stream_list(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Prints out comprehensive listing of streams
    """
    log.debug("stream.list")
    streams: List[Stream] = await amplipi.get_streams()
    list_streams(streams)


async def do_stream_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Stream json represenatation by stream_id
    """
    log.debug(f"stream.get({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    stream: Stream = await amplipi.get_stream(args.streamid)
    write_out(stream.json(**json_ser_kwargs), args.outfile)


async def do_stream_getall(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Streams json represenatation
    """
    log.debug("stream.getall()")
    streams: List[Stream] = await amplipi.get_streams()
    write_out(model_list_to_json(streams), args.outfile)


async def do_stream_set(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Update a stream(id)'s configuration
    """
    log.debug(f"stream.set({args.streamid}, input={args.input if args.input is not None else '«stdin»'})")
    assert 0 <= args.streamid, "stream id must be > 0"

    def validate(input: dict):
        log.debug(f"validating stream_update kwargs: {input}")
        assert len(input.keys()) > 0, "no actual stream values to be set"
    stream_update: StreamUpdate = instantiate_model(StreamUpdate, args.infile, args.input, validate)
    await amplipi.set_stream(args.streamid, stream_update)  # ignoring status return value


async def do_stream_new(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Create a new stream
    """
    log.debug(f"stream.create(input={args.input if args.input is not None else '«stdin»'})")

    def validate(input: dict):
        log.debug(f"validating stream_update kwargs: {input}")
        assert all((input.get('name'), input.get('type'))), "stream needs a name and a type"
    stream: Stream = instantiate_model(Stream, args.infile, args.input, validate)
    await amplipi.create_stream(stream)  # ignoring status return value


async def do_stream_del(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Delete the stream by streamid
    """
    log.debug(f"stream.delete({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.delete_stream(args.streamid)  # ignoring status return value


async def do_stream_play(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Play the stream by streamid
    """
    log.debug(f"stream.play({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.play_stream(args.streamid)  # ignoring status return value


async def do_stream_pause(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Pauses the stream by streamid
    """
    log.debug(f"stream.pause({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.pause_stream(args.streamid)  # ignoring status return value


async def do_stream_stop(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Stops the stream by streamid
    """
    log.debug(f"stream.stop({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.stop_stream(args.streamid)  # ignoring status return value


async def do_stream_next(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Next item in the stream by streamid
    """
    log.debug(f"stream.next({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.next_stream(args.streamid)  # ignoring status return value


async def do_stream_prev(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Previous item in the stream by streamid
    """
    log.debug(f"stream.previous({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.previous_stream(args.streamid)  # ignoring status return value


async def do_stream_stationchange(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ StationChange on the stream by streamid
    """
    log.debug(f"stream.station_change({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    await amplipi.station_change_stream(args.streamid, args.station)  # ignoring status return value


# -- preset section
async def do_preset_list(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Prints out comprehensive listing of presets
    """
    log.debug("preset.list")
    preset: List[Preset] = await amplipi.get_presets()
    list_presets(preset)


async def do_preset_get(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Preset json representation by preset_id
    """
    log.debug(f"preset.get({args.presetid})")
    assert 0 <= args.presetid, "preset id must be > 0"
    preset: Preset = await amplipi.get_preset(args.presetid)
    write_out(preset.json(**json_ser_kwargs), args.outfile)


async def do_preset_getall(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Gets Presets json representation
    """
    log.debug("preset.getall()")
    presets: List[Preset] = await amplipi.get_presets()
    write_out(model_list_to_json(presets), args.outfile)


async def do_preset_set(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Update a preset(id)'s configuration
    """
    log.debug(f"preset.set({args.presetid}, «stdin»)")
    assert 0 <= args.presetid, "stream id must be > 0"
    preset_update: PresetUpdate = instantiate_model(PresetUpdate, args.infile, args.input)
    await amplipi.set_preset(args.presetid, preset_update)  # ignoring status return value


async def do_preset_new(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Create a new preset
    """
    log.debug(f"preset.create(input={args.input if args.input is not None else '«stdin»'})")
    preset: Preset = instantiate_model(Preset, args.infile)
    await amplipi.create_preset(preset)  # ignoring status return value


async def do_preset_del(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Delete the preset by presetid
    """
    log.debug(f"preset.delete({args.presetid})")
    assert 0 <= args.presetid, "preset id must be > 0"
    await amplipi.delete_preset(args.presetid)  # ignoring status return value


async def do_preset_load(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Activate (load) the Preset by presetid
    """
    log.debug(f"preset.load({args.presetid})")
    assert 0 <= args.presetid, "preset id must be > 0"
    await amplipi.load_preset(args.presetid)  # ignoring status return value


# -- announce section
async def do_announce(args: Namespace, amplipi: AmpliPi, shell: bool, **kwargs):
    """ Plays announcement
    """
    def validate(input: dict):
        log.debug(f"validating announcement kwargs: {input}")
        assert validators.url(input['media']), "media_url must be a valid URL"
        assert 'vol_f' not in input or 0.0 <= input['vol_f'] <= 1.0, "vol_f must be in range 0.0..1.0"

    log.debug(f"announce(input={args.input if args.input is not None else '«stdin»'})")
    announcement: Announcement = instantiate_model(Announcement, args.infile, args.input, validate)
    # TODO
    #   after PR #14 is merged - we can use the per-call timeout feature to override timeout in this call
    #   Note: only makes sense in shell mode as only then the amplipi object gets reused
    await amplipi.announce(announcement)   # returns Status object which we ignore


# -- shell section
async def do_shell(args: Namespace, amplipi: AmpliPi, shell: bool, argsparser: ArgumentParser, **kwargs):
    """ Evaluates entering interactive mode
    """
    if shell is True:
        print("Entering a nested shell is not supported - command ignored.")
        return
    if args.script is not None:
        await script_shell(args.script, amplipi, argsparser)
        return
    # else
    await interactive_shell(amplipi, argsparser)


async def script_shell(script_file: str, amplipi: AmpliPi, argsparser: ArgumentParser):
    """ Executes the command-lines in the script_file
    """
    with open(script_file, 'r') as script:
        while True:
            cmdline: str = script.readline()
            if not cmdline:
                log.debug("EOF script to shell")
                break
            # else
            await shell_cmd_exec(cmdline.strip(), amplipi, argsparser)


async def interactive_shell(amplipi: AmpliPi, argsparser: ArgumentParser):
    """ Enters interactive mode to execute multiple consecutive commands while reusing the amplipi client
    """
    assert argsparser is not None, "shell requires an actual argsparser"
    print("Entering shell mode - Use «ctrl» + «d» to finish.")
    prompt = "ampsh > "
    while True:                # read input
        cmdline: Optional[str] = None
        try:
            cmdline = input(prompt)
        except EOFError:       # triggered by ctrl-d
            log.debug("EOF shell")
            print()            # just add a newline
            break              # and break

        if cmdline == 'exit':  # allow this alternative to ctrl-d
            log.debug("exit shell")
            break              # so do as requested
        # else
        await shell_cmd_exec(cmdline, amplipi, argsparser)
    log.debug("ending interactive shell")


async def shell_cmd_exec(cmdline: str, amplipi: AmpliPi, argsparser: ArgumentParser):
    """ Executes one line of pyamplipi-shell commands
    """
    if len(cmdline) == 0 or cmdline[0] == '#':
        return    # ignore empty lines or comment lines
    try:  # to actually call the requested function
        cmdargs = argsparser.parse_args(cmdline.split())
        log.debug(f"cmdargs == {cmdargs}")
        if cmdargs.func is not None and callable(cmdargs.func):
            await cmdargs.func(cmdargs, amplipi, shell=True)
            return
    except ArgumentError as e:
        print(e)
    except (AssertionError, APIError) as e:
        log.error(e)
        print(e)
    except ServerDisconnectedError as e:
        log.exception(e)
        print("server disconnected - pls retry")
    except Exception as e:
        log.exception(e)
        print(e)


def instantiate_model(model_cls: ModelMetaclass, infile: str, _input: Optional[Dict[str, Any]] = None, validate: Optional[Callable] = None):
    """ Instatiates the passed BaseModel based on:
      (1) either the passed input dict (if not None) merged with env var defaults
      (2) either a json representation read from stdin
    """
    # TODO revisit this approach in the case input is not None
    #    -- BaseModel.parse_obj(dict) is probably better suited than the current BaseModel(**kwargs)
    #    -- the whole parse_valuestr can probably be avoided
    #    -- more complex structures could be covered by pydantic itself
    #    -- the validation is then just up to pydantic too
    #    -- only would need a ParseDict thingy that can build nested dictionaries
    if _input is not None:
        _input = merge_model_kwargs(model_cls, _input)
        if validate is not None:
            validate(_input)
        return model_cls(**_input)
    # else read the object from stdin (json)
    return model_cls.parse_obj(json.loads(read_in(infile)))


def merge_model_kwargs(model_cls: ModelMetaclass, input: dict) -> Dict[str, Any]:
    """ Builds the kwargs needed to construct the passed BaseModel by merging the passed input dict
    with possible available environment variables with key following this pattern:
        "AMPLIPI_" + «name of BaseModel» + "_" + «name of field in BaseModel» (in all caps)
    """
    def envvar(name):
        envkey = f"AMPLIPI_{model_cls.__name__}_{name}".upper()
        return os.getenv(envkey)
    kwargs = dict()
    for name, modelfield in model_cls.__fields__.items():
        value_str: str = input.get(name, envvar(name))
        if value_str is not None and type(value_str) == str and len(value_str) > 0:
            value = parse_valuestr(value_str, modelfield)
            log.debug(f"converted {value_str} to {value} for {modelfield.type_}")
            kwargs[name] = value
    return kwargs


# helper functions for the arguments parsing
def parse_valuestr(val_str: str, modelfield: ModelField):
    """ Uses the pydantic defined Modelfield to correctly parse CLI passed string-values to typed values
    Supports simple types and lists of them
    """
    convertor = modelfield.type_
    if convertor == bool:
        def boolconvertor(s):
            return len(s) > 0 and s.lower() in ('y', 'yes', '1', 'true', 'on')
        convertor = boolconvertor
    if modelfield.outer_type_.__name__ == 'List':
        assert val_str[0] == '[' and val_str[-1] == ']', "expected array-value needs to be surrounded with []"
        val_str = val_str[1:-1]
        return [convertor(v.strip()) for v in val_str.split(',')]
    # else
    return convertor(val_str)


class ParseDict(Action):
    """ Allows -i --input key-val arguments to be converted into dict.
    see [github](https://gist.github.com/fralau/061a4f6c13251367ef1d9a9a99fb3e8d?permalink_comment_id=4134590#gistcomment-4134590)
    """
    def __call__(self, parser, namespace, values, option_string=None):
        d = getattr(namespace, self.dest) or {}

        if values:
            for item in values:
                split_items = item.split("=", 1)
                key = split_items[0].strip()  # we remove blanks around keys, as is logical
                value = split_items[1]
                d[key] = value

        setattr(namespace, self.dest, d)


def add_force_argument(ap: ArgumentParser):
    """ Adds the --force argument in a conistent way to commands that need explicite or interactive confirmation
    """
    ap.add_argument(
        "--force", "-f",
        action='store_true',
        help="force the command to be executed without interaction.")


def add_id_argument(ap: ArgumentParser, model_cls: ModelMetaclass):
    """ Adds the --input argument in a consistent way
    """
    name = model_cls.__name__.lower()
    ap.add_argument(
        f"{name}id",
        action='store', type=int, metavar="ID",
        help="identifier of the {name} (integer)")


def add_input_arguments(ap: ArgumentParser, model_cls: ModelMetaclass, too_complex_for_cli_keyvals: bool = False):
    """ Adds the --input -i and --infile -I  argument in a consistent way
    The -i argument takes key-value pairs to construct models rather then provide those in json via stdin (for simple models only)
    The -I argument specifies an input file to use in stead of stdin
    """
    ap.add_argument(
        '--infile', '-I',
        action='store',
        metavar="FILE",
        help="provide the file to be used as input source in stead of stdin.",
    )
    if too_complex_for_cli_keyvals:
        return
    # else allow key-val --input
    ap.add_argument(
        '--input', '-i',
        action=ParseDict,
        metavar="KEY=VALUE",
        nargs="*",
        help=f"Set any of the fields ({', '.join(model_cls.__fields__.keys())}) to the {model_cls.__name__} object inline."
        " (do not put spaces before or after the = sign). "
        " Use double quotes to let values have spaces."
        ' foo="this is a sentence".'
        " Using this avoids passing the json representation via stdin.",
    )


def add_output_arguments(ap: ArgumentParser):
    """ Adds the --outile -O argument in a consistent way
    The argument specifies the output file to use in stead of stdout
    """
    ap.add_argument(
        '--outfile', '-O',
        action='store',
        metavar="FILE",
        help="provide the file to be used as output target in stead of stdout.",
    )


def get_arg_parser() -> ArgumentParser:
    """ Defines the arguments to this module's __main__ cli script
    by using Python's [argparse](https://docs.python.org/3/library/argparse.html)
    """
    parent_ap = ArgumentParser(
        prog='pyamplipi',
        description='CLI for interactive amplipi /api calls',
        formatter_class=ArgumentDefaultsHelpFormatter,
        exit_on_error=False,
    )

    parent_ap.add_argument(
        '-l', '--logconf',
        metavar="LOGCONF_FILE.yml",
        type=str,
        action='store',
        help='The config file for the Logging in yml format',
    )
    parent_ap.add_argument(
        '-a', '--amplipi',
        metavar="API_URL",
        type=str,
        action='store',
        help='The Base URL for the amplipi service endpoint (should typically end in /api)',
        default=os.getenv('AMPLIPI_API_URL')
    )
    parent_ap.add_argument(
        '-t', '--timeout',
        metavar="SECONDS",
        type=int,
        action='store',
        help='The timeout in seconds (int) to be applied in the client.',
        default=os.getenv('AMPLIPI_TIMEOUT')
    )
    # todo should we consider -f --format json(default)|yml|pickle... other formats for the in/out?

    topics_subs = parent_ap.add_subparsers(
        title='topics / entities to manage',
        required=True,
        metavar="TOPIC",
    )

    # create the various topic branches
    topic_status_ap = topics_subs.add_parser(
        "status", aliases=['stat', 'state', 'conf', 'config', 'sys', 'system'],
        exit_on_error=False,
        help="view/store the general status")
    topic_source_ap = topics_subs.add_parser(
        "sources", aliases=['src', 'source'],
        exit_on_error=False,
        help="configure the various input sources")
    topic_zone_ap = topics_subs.add_parser(
        "zones", aliases=['zn', 'zone'],
        exit_on_error=False,
        help="configure the available output zones")
    topic_group_ap = topics_subs.add_parser(
        "groups", aliases=['grp', 'group'],
        exit_on_error=False,
        help="manage the output groups")
    topic_stream_ap = topics_subs.add_parser(
        "streams", aliases=['str', 'stream'],
        exit_on_error=False,
        help="manage the available streams")
    topic_announce_ap = topics_subs.add_parser(
        "announce", aliases=['ann', 'play'],
        exit_on_error=False,
        help="play announcements")
    topic_preset_ap = topics_subs.add_parser(
        "presets", aliases=['pr', 'pre', 'preset'],
        exit_on_error=False,
        help="manage the presets")
    topic_shell_ap = topics_subs.add_parser(
        "shell", aliases=['sh'],
        exit_on_error=False,
        help="enter into interactive shell mode")

    action_supbarser_kwargs: Dict[str, Any] = dict(title='actions to perform', required=True, metavar="ACTION",)

    # details of the status handling branch
    status_subs = topic_status_ap.add_subparsers(**action_supbarser_kwargs)
    # -- status list
    status_subs.add_parser('list', aliases=['ls'], help="list status overview").set_defaults(func=do_status_list)
    # -- status get
    get_status_ap = status_subs.add_parser('get', help="dumps status json to stdout")
    add_output_arguments(get_status_ap)
    get_status_ap.set_defaults(func=do_status_get)
    # -- config load (~≃ status set)
    load_config_ap = status_subs.add_parser('set', aliases=['load'], help="overwrites status json with input from stdin")
    add_force_argument(load_config_ap)
    add_input_arguments(load_config_ap, Status, too_complex_for_cli_keyvals=True)
    load_config_ap.set_defaults(func=do_config_load)
    # -- factory-reset
    factory_reset_ap = status_subs.add_parser('factory', aliases=['fact'], help="resets the configuration to factory defaults")
    add_force_argument(factory_reset_ap)
    factory_reset_ap.set_defaults(func=do_factory_reset)
    # -- system-reset
    system_reset_ap = status_subs.add_parser('reset', help="resets the system firmware, reloads the current config")
    add_force_argument(system_reset_ap)
    system_reset_ap.set_defaults(func=do_system_reset)
    # -- system-reboot
    system_reboot_ap = status_subs.add_parser('reboot', aliases=['boot', 'restart'], help="reboots the system OS")
    add_force_argument(system_reboot_ap)
    system_reboot_ap.set_defaults(func=do_system_reboot)
    # -- system-shutdown
    system_shutdown_ap = status_subs.add_parser('shutdown', aliases=['shut', 'stop'], help="shuts down the system OS")
    add_force_argument(system_shutdown_ap)
    system_shutdown_ap.set_defaults(func=do_system_shutdown)
    # -- status info
    info_status_ap = status_subs.add_parser('info', help="dumps status-info json to stdout")
    add_output_arguments(info_status_ap)
    info_status_ap.set_defaults(func=do_info_get)

    # details of the source handling branch
    source_subs = topic_source_ap.add_subparsers(**action_supbarser_kwargs)
    # -- source list
    source_subs.add_parser('list', aliases=['ls'], help="list sources overview").set_defaults(func=do_source_list)
    # -- source get
    get_source_ap = source_subs.add_parser('get', help="dumps source configuration json to stdout")
    add_id_argument(get_source_ap, Source)
    add_output_arguments(get_source_ap)
    get_source_ap.set_defaults(func=do_source_get)
    # -- source get-all
    getall_source_ap = source_subs.add_parser('get-all', aliases=['getall'], help="dumps source configuration json to stdout")
    add_output_arguments(getall_source_ap)
    getall_source_ap.set_defaults(func=do_source_getall)
    # -- source set
    set_source_ap = source_subs.add_parser('set', help="overwrites source configuration with json input from stdin")
    add_id_argument(set_source_ap, Source)
    add_input_arguments(set_source_ap, Source)
    set_source_ap.set_defaults(func=do_source_set)
    # -- source getimg
    getimg_source_ap = source_subs.add_parser('img', help="gets a square jpeg image of what is playing on the source")
    add_id_argument(getimg_source_ap, Source)
    getimg_source_ap.add_argument('size', type=int, help="the size (sizexsize) in pixels of the image to be returned")
    add_output_arguments(getimg_source_ap)
    getimg_source_ap.set_defaults(func=do_source_getimg)

    # details of the zone handling branch
    zone_subs = topic_zone_ap.add_subparsers(**action_supbarser_kwargs)
    # -- zone list
    zone_subs.add_parser('list', aliases=['ls'], help="list zones overview").set_defaults(func=do_zone_list)
    # -- zone get
    get_zone_ap = zone_subs.add_parser('get', help="dumps zone configuration json to stdout")
    add_id_argument(get_zone_ap, Zone)
    add_output_arguments(get_zone_ap)
    get_zone_ap.set_defaults(func=do_zone_get)
    # -- zone getall
    getall_zone_ap = zone_subs.add_parser('getall', help="dumps zone configuration json to stdout")
    add_output_arguments(getall_zone_ap)
    getall_zone_ap.set_defaults(func=do_zone_getall)
    # -- zone set
    set_zone_ap = zone_subs.add_parser('set', help="overwrites zone configuration with json input from stdin")
    add_id_argument(set_zone_ap, Zone)
    add_input_arguments(set_zone_ap, ZoneUpdate)
    set_zone_ap.set_defaults(func=do_zone_set)
    # -- zone setall
    setall_zone_ap = zone_subs.add_parser('setall', help="overwrites zone configuration with json input from stdin")
    add_input_arguments(setall_zone_ap, MultiZoneUpdate, too_complex_for_cli_keyvals=True)
    setall_zone_ap.set_defaults(func=do_zone_setall)

    # details of the group handling branch
    group_subs = topic_group_ap.add_subparsers(**action_supbarser_kwargs)
    # -- group list
    group_subs.add_parser('list', aliases=['ls'], help="list groups overview").set_defaults(func=do_group_list)
    # -- group get
    get_group_ap = group_subs.add_parser('get', help="dumps group configuration json to stdout")
    add_id_argument(get_group_ap, Group)
    add_output_arguments(get_group_ap)
    get_group_ap.set_defaults(func=do_group_get)
    # -- group getall
    getall_group_ap = group_subs.add_parser('getall', help="dumps group configuration json to stdout")
    add_output_arguments(getall_group_ap)
    getall_group_ap.set_defaults(func=do_group_getall)
    # -- group set
    set_group_ap = group_subs.add_parser('set', help="overwrites group configuration with json input from stdin")
    add_id_argument(set_group_ap, Group)
    add_input_arguments(set_group_ap, GroupUpdate)
    set_group_ap.set_defaults(func=do_group_set)
    # -- group new
    new_group_ap = group_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new group based on the json input from stdin"
        )
    add_input_arguments(new_group_ap, Group)
    new_group_ap.set_defaults(func=do_group_new)
    # -- group del
    del_group_ap = group_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified group")
    add_id_argument(del_group_ap, Group)
    del_group_ap.set_defaults(func=do_group_del)

    # details of the stream handling branch
    stream_subs = topic_stream_ap.add_subparsers(**action_supbarser_kwargs)
    # -- stream list
    stream_subs.add_parser('list', aliases=['ls'], help="list streams overview").set_defaults(func=do_stream_list)
    # -- stream get
    get_stream_ap = stream_subs.add_parser('get', help="dumps stream configuration json to stdout")
    add_id_argument(get_stream_ap, Stream)
    add_output_arguments(get_stream_ap)
    get_stream_ap.set_defaults(func=do_stream_get)
    # -- stream getall
    getall_stream_ap = stream_subs.add_parser('getall', help="dumps stream configuration json to stdout")
    add_output_arguments(getall_stream_ap)
    getall_stream_ap.set_defaults(func=do_stream_getall)
    # -- stream set
    set_stream_ap = stream_subs.add_parser('set', help="overwrites stream configuration with json input from stdin")
    add_id_argument(set_stream_ap, Stream)
    add_input_arguments(set_stream_ap, StreamUpdate)
    set_stream_ap.set_defaults(func=do_stream_set)
    # -- stream new
    new_stream_ap = stream_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new stream based on the json input from stdin"
        )
    add_input_arguments(new_stream_ap, Stream)
    new_stream_ap.set_defaults(func=do_stream_new)
    # -- stream del
    del_stream_ap = stream_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified stream")
    add_id_argument(del_stream_ap, Stream)
    del_stream_ap.set_defaults(func=do_stream_del)
    # -- stream play
    play_stream_ap = stream_subs.add_parser('play', aliases=['pl'], help="plays the specified stream")
    add_id_argument(play_stream_ap, Stream)
    play_stream_ap.set_defaults(func=do_stream_play)
    # -- stream pause
    pause_stream_ap = stream_subs.add_parser('pause', aliases=['ps'], help="pauses the specified stream")
    add_id_argument(pause_stream_ap, Stream)
    pause_stream_ap.set_defaults(func=do_stream_pause)
    # -- stream stop
    stop_stream_ap = stream_subs.add_parser('stop', aliases=['st'], help="stops the specified stream")
    add_id_argument(stop_stream_ap, Stream)
    stop_stream_ap.set_defaults(func=do_stream_stop)
    # -- stream next
    next_stream_ap = stream_subs.add_parser('next', aliases=['fwd', '»'], help="forwards the specified stream to next item")
    add_id_argument(next_stream_ap, Stream)
    next_stream_ap.set_defaults(func=do_stream_next)
    # -- stream prev
    prev_stream_ap = stream_subs.add_parser(
        'previous', aliases=['prev', 'back', 'bwd', '«'],
        help="reverses the specified stream back to the previous item")
    add_id_argument(prev_stream_ap, Stream)
    prev_stream_ap.set_defaults(func=do_stream_prev)
    # -- stream station change
    station_stream_ap = stream_subs.add_parser(
        'station', aliases=['pandora', 'stat'],
        help="changes the pandora-stream to the station")
    add_id_argument(station_stream_ap, Stream)
    station_stream_ap.add_argument('station', action='store', type=int, help="pandora station id")
    station_stream_ap.set_defaults(func=do_stream_stationchange)

    # details of the preset handling branch
    preset_subs = topic_preset_ap.add_subparsers(**action_supbarser_kwargs)
    # -- preset list
    preset_subs.add_parser('list', aliases=['ls'], help="list presets overview").set_defaults(func=do_preset_list)
    # -- preset get
    get_preset_ap = preset_subs.add_parser('get', help="dumps preset configuration json to stdout")
    add_id_argument(get_preset_ap, Preset)
    add_output_arguments(get_preset_ap)
    get_preset_ap.set_defaults(func=do_preset_get)
    # -- preset getall
    getall_preset_ap = preset_subs.add_parser('getall', help="dumps preset configuration json to stdout")
    add_output_arguments(getall_preset_ap)
    getall_preset_ap.set_defaults(func=do_preset_getall)
    # -- preset set
    set_preset_ap = preset_subs.add_parser('set', help="overwrites preset configuration with json input from stdin")
    add_id_argument(set_preset_ap, Preset)
    add_input_arguments(set_preset_ap, PresetUpdate)
    set_preset_ap.set_defaults(func=do_preset_set)
    # -- preset new
    new_preset_ap = preset_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new preset based on the json input from stdin"
        )
    add_input_arguments(new_preset_ap, Preset)
    new_preset_ap.set_defaults(func=do_preset_new)
    # -- preset del
    del_preset_ap = preset_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified preset")
    add_id_argument(del_preset_ap, Preset)
    del_preset_ap.set_defaults(func=do_preset_del)
    # -- preset load
    load_preset_ap = preset_subs.add_parser('load', aliases=['on', 'activate'], help="activates the specified preset")
    add_id_argument(load_preset_ap, Preset)
    load_preset_ap.set_defaults(func=do_preset_load)

    # details of the announce handling branch
    add_input_arguments(topic_announce_ap, Announcement)
    topic_announce_ap.set_defaults(func=do_announce)

    # details of the shell branch
    topic_shell_ap.add_argument("script", action='store', nargs='?', help="the script-file to be interpreted")
    topic_shell_ap.set_defaults(func=do_shell)

    return parent_ap


# helper functions for the logging config
def yaml_load_file(file):
    """ Loads a yaml based config file
    """
    if file is None:
        log.debug("can not load unspecified yaml file")
        return None
    # else
    try:
        with open(file, 'r') as yml_file:
            return yaml.load(yml_file, Loader=yaml.SafeLoader)
    except Exception as e:
        log.exception(e)
        return dict()


def enable_logging(logconf=None):
    """Configures logging based on logconf specified through .env ${LOGCONF}
    """
    logconf = os.getenv("LOGCONF") if logconf is None else None
    if logconf is None or logconf == '':
        return
    # else
    logging.config.dictConfig(yaml_load_file(logconf))
    log.info(f"Logging enabled according to config in {logconf}")


# helper function to instantiate the client
def make_amplipi(args: Namespace) -> AmpliPi:
    """ Constructs the amplipi client
    """
    endpoint: str = args.amplipi
    timeout: int = args.timeout
    # in shell modus we got frequent server-disconnected-errors - injecting this custom session avoids that
    connector: TCPConnector = TCPConnector(force_close=True)
    http_session: ClientSession = ClientSession(connector=connector)
    return AmpliPi(endpoint, timeout=timeout, http_session=http_session)


# main script entrypoint
def main():
    exitcode = 0  # assuming all will be well
    load_dotenv()
    ap = get_arg_parser()
    args: Namespace = None
    try:
        args = ap.parse_args()
    except ArgumentError as e:  # manual error handling as per https://docs.python.org/3/library/argparse.html#exit-on-error
        ap.print_help()
        log.error(e)
        log.debug("exit(1) due to bad arguments on cli")
        sys.exit(1)

    enable_logging(logconf=args.logconf)
    amplipi = make_amplipi(args)

    # setup async wait construct for main routines
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        # trigger the actual called action-function (async) and wait for it
        loop.run_until_complete(args.func(args, amplipi, shell=False, argsparser=ap))
    except (AssertionError, APIError) as e:
        log.error(e)
        print(e)
        exitcode = 1
    except Exception as e:
        log.exception(e)
        print(e)
        exitcode = 1
    finally:
        loop.run_until_complete(amplipi.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        log.debug(f"exit({exitcode})")
        sys.exit(exitcode)


if __name__ == '__main__':
    main()
