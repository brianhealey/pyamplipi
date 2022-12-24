import logging
import asyncio
import sys
import os
import yaml
import datetime
from dotenv import load_dotenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from typing import List
from tabulate import tabulate
from textwrap import indent
from pyamplipi.models import Status, Info, Source, Zone, Group, Stream, Preset  # , Announcement
from pyamplipi.amplipi import AmpliPi
from pyamplipi.error import APIError


# constants
log = logging.getLogger(__name__)      # central logging channel
json_ser_kwargs = dict(indent=2)     # arguments to serialise the json


# text formatters
def em(msg: str) -> str: return f'\033[4m{msg}\033[0m'                                  # underline text for emphasis
def table(d, h) -> str: return indent(tabulate(d, h, tablefmt='rounded_outline'), '  ')  # make a nice indented table


# list methods dumping comprehensive output to stdout
def list_info(info: Info):
    print(em("Info:"))
    headers = ["Filename", "Version", "Mock Controls", "Mock Streams"]
    data = list()
    data.append([info.config_file, info.version, info.mock_ctrl, info.mock_streams])
    print(table(data, headers))


def list_sources(sources: List[Source]):
    print(em(f"Sources[{len(sources)}]"))
    headers = ["ID", "Name", "Input", "Info", "State"]
    data = [[s.id, s.name, s.input, s.info.name, s.info.state] for s in sources]
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
    list_info(status.info)
    list_sources(status.sources)
    list_zones(status.zones)
    list_groups(status.groups)
    list_streams(status.streams)
    list_presets(status.presets)


# actual service-methods
async def do_placeholder(args: Namespace, amplipi: AmpliPi):  # placeholder during dev - to be removed when completed
    log.warning(f"todo handle command args --> \n  args = {args}\n  ammplipi = {amplipi}")


async def do_status_list(args: Namespace, amplipi: AmpliPi):
    log.debug("status.list")
    status: Status = await amplipi.get_status()
    list_status(status)


async def do_status_get(args: Namespace, amplipi: AmpliPi):
    log.debug("status.get")
    status: Status = await amplipi.get_status()
    print(status.json(**json_ser_kwargs))

# async def do_status_set(args: Namespace, amplipi: AmpliPi):


async def do_source_list(args: Namespace, amplipi: AmpliPi):
    log.debug("source.list")
    sources: List[Source] = await amplipi.get_sources()
    list_sources(sources)


async def do_source_get(args: Namespace, amplipi: AmpliPi):
    log.debug(f"source.get({args.sourceid})")
    assert 0 <= args.sourceid <= 3, "source id must be in range 0..3"
    source: Source = await amplipi.get_source(args.sourceid)
    print(source.json(**json_ser_kwargs))

# async def do_source_set(args: Namespace, amplipi: AmpliPi):


async def do_zone_list(args: Namespace, amplipi: AmpliPi):
    log.debug("zone.list")
    zones: List[Zone] = await amplipi.get_zones()
    list_zones(zones)


async def do_zone_get(args: Namespace, amplipi: AmpliPi):
    log.debug(f"zone.get({args.zoneid})")
    assert 0 <= args.zoneid <= 35, "zone id must be in range 0..35"
    zone: Zone = await amplipi.get_zone(args.zoneid)
    print(zone.json(**json_ser_kwargs))

# async def do_zone_set(args: Namespace, amplipi: AmpliPi):


async def do_group_list(args: Namespace, amplipi: AmpliPi):
    log.debug("group.list")
    groups: List[Group] = await amplipi.get_groups()
    list_groups(groups)


async def do_group_get(args: Namespace, amplipi: AmpliPi):
    log.debug(f"group.get({args.groupid})")
    assert 0 <= args.groupid, "group id must be > 0"
    group: Group = await amplipi.get_group(args.groupid)
    print(group.json(**json_ser_kwargs))

# async def do_group_set(args: Namespace, amplipi: AmpliPi):
# async def do_group_load(args: Namespace, amplipi: AmpliPi):
# async def do_group_new(args: Namespace, amplipi: AmpliPi):
# async def do_group_del(args: Namespace, amplipi: AmpliPi):


async def do_stream_list(args: Namespace, amplipi: AmpliPi):
    log.debug("stream.list")
    streams: List[Stream] = await amplipi.get_streams()
    list_streams(streams)

# async def do_announce(args: Namespace, amplipi: AmpliPi):


async def do_stream_get(args: Namespace, amplipi: AmpliPi):
    log.debug(f"stream.get({args.streamid})")
    assert 0 <= args.streamid, "stream id must be > 0"
    stream: Stream = await amplipi.get_stream(args.streamid)
    print(stream.json(**json_ser_kwargs))


# async def do_stream_set(args: Namespace, amplipi: AmpliPi):
# async def do_stream_new(args: Namespace, amplipi: AmpliPi):
# async def do_stream_del(args: Namespace, amplipi: AmpliPi):
# async def do_stream_play(args: Namespace, amplipi: AmpliPi):
# async def do_stream_pause(args: Namespace, amplipi: AmpliPi):
# async def do_stream_stop(args: Namespace, amplipi: AmpliPi):
# async def do_stream_next(args: Namespace, amplipi: AmpliPi):
# async def do_stream_prev(args: Namespace, amplipi: AmpliPI):


async def do_preset_list(args: Namespace, amplipi: AmpliPi):
    log.debug("preset.list")
    preset: List[Preset] = await amplipi.get_presets()
    list_presets(preset)


async def do_preset_get(args: Namespace, amplipi: AmpliPi):
    log.debug(f"preset.get({args.presetid})")
    assert 0 <= args.presetid, "preset id must be > 0"
    preset: Preset = await amplipi.get_preset(args.presetid)
    print(preset.json(**json_ser_kwargs))


# async def do_preset_set(args: Namespace, amplipi: AmpliPi):
# async def do_preset_new(args: Namespace, amplipi: AmpliPi):
# async def do_preset_del(args: Namespace, amplipi: AmpliPi):


def get_arg_parser():
    """ Defines the arguments to this module's __main__ cli script
    by using Python's [argparse](https://docs.python.org/3/library/argparse.html)
    """
    parent_ap = ArgumentParser(
        prog='pyamplipi',
        description='CLI for interactive amplipi /api calls',
        formatter_class=ArgumentDefaultsHelpFormatter,
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
        help='The timeout in seconds (int) to be applid in the client.',
        default=os.getenv('AMPLIPI_TIMEOUT')
    )
    # todo should we consider -f --format json(default)|yml|pickle... other formats for the in/out?

    topics_subs = parent_ap.add_subparsers(
        title='topics / entities to manage',
        required=True,
        metavar="TOPIC",
    )

    # create the various topic branches
    topic_status_ap = topics_subs.add_parser("status", aliases=['stat', 'state'], help="view/store the general status")
    topic_source_ap = topics_subs.add_parser("sources", aliases=['src', 'source'], help="configure the various input sources")
    topic_zone_ap = topics_subs.add_parser("zones", aliases=['zn', 'zone'], help="configure the available output zones")
    topic_group_ap = topics_subs.add_parser("groups", aliases=['grp', 'group'], help="manage the output groups")
    topic_stream_ap = topics_subs.add_parser("streams", aliases=['str', 'stream'], help="manage the available streams")
    topic_announce_ap = topics_subs.add_parser("announce", aliases=['ann', 'play'], help="play announcements")
    topic_preset_ap = topics_subs.add_parser("presets", aliases=['pr', 'pre', 'preset'], help="manage the presets")

    # details of the status handling branch
    status_subs = topic_status_ap.add_subparsers(title='actions to perform', required=True, metavar="ACTION",)
    # -- status list
    status_subs.add_parser('list', aliases=['ls'], help="list status overview").set_defaults(func=do_status_list)
    # -- status get
    status_subs.add_parser('get', help="dumps status json to stdout").set_defaults(func=do_status_get)
    # -- status set
    status_subs.add_parser('set', help="overwrites status json with input from stdin").set_defaults(func=do_placeholder)

    # details of the source handling branch
    source_subs = topic_source_ap.add_subparsers(title='actions to perform', required=True, metavar="ACTION",)
    # -- source list
    source_subs.add_parser('list', aliases=['ls'], help="list sources overview").set_defaults(func=do_source_list)
    # -- source get
    get_source_ap = source_subs.add_parser('get', help="dumps source configuration json to stdout")
    get_source_ap.add_argument("sourceid", action='store', type=int, metavar="ID", help="identifier of the source")
    get_source_ap.set_defaults(func=do_source_get)
    # -- source set
    set_source_ap = source_subs.add_parser('set', help="overwrites source configuration with json input from stdin")
    set_source_ap.add_argument("sourceid", action='store', type=int, metavar="ID", help="identifier of the source")
    set_source_ap.set_defaults(func=do_placeholder)

    # details of the zone handling branch
    zone_subs = topic_zone_ap.add_subparsers(title='actions to perform', required=True, metavar="ACTION",)
    # -- zone list
    zone_subs.add_parser('list', aliases=['ls'], help="list zones overview").set_defaults(func=do_zone_list)
    # -- zone get
    get_zone_ap = zone_subs.add_parser('get', help="dumps zone configuration json to stdout")
    get_zone_ap.add_argument("zoneid", action='store', type=int, metavar="ID", help="identifier of the zone")
    get_zone_ap.set_defaults(func=do_zone_get)
    # -- zone set
    set_zone_ap = zone_subs.add_parser('set', help="overwrites zone configuration with json input from stdin")
    set_zone_ap.add_argument("zoneid", action='store', type=int, metavar="ID", help="identifier of the zone")
    set_zone_ap.set_defaults(func=do_placeholder)

    # details of the group handling branch
    group_subs = topic_group_ap.add_subparsers(title='actions to perform', required=True, metavar="ACTION",)
    # -- group list
    group_subs.add_parser('list', aliases=['ls'], help="list groups overview").set_defaults(func=do_group_list)
    # -- group get
    get_group_ap = group_subs.add_parser('get', help="dumps group configuration json to stdout")
    get_group_ap.add_argument("groupid", action='store', type=int, metavar="ID", help="identifier of the group")
    get_group_ap.set_defaults(func=do_group_get)
    # -- group set
    set_group_ap = group_subs.add_parser('set', help="overwrites group configuration with json input from stdin")
    set_group_ap.add_argument("groupid", action='store', type=int, metavar="ID", help="identifier of the group")
    set_group_ap.set_defaults(func=do_placeholder)
    # -- group load
    load_group_ap = group_subs.add_parser('load', help="overwrites group configuration with json input from stdin")
    load_group_ap.add_argument("groupid", action='store', type=int, metavar="ID", help="identifier of the group")
    load_group_ap.set_defaults(func=do_placeholder)
    # -- group new
    group_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new group based on the json input from stdin"
        ).set_defaults(func=do_placeholder)
    # -- group del
    del_group_ap = group_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified group")
    del_group_ap.add_argument("groupid", action='store', type=int, metavar="ID", help="identifier of the group")
    del_group_ap.set_defaults(func=do_placeholder)

    # details of the stream handling branch
    stream_subs = topic_stream_ap.add_subparsers(title='actions to perform', required=True, metavar="ACTION",)
    # -- stream list
    stream_subs.add_parser('list', aliases=['ls'], help="list streams overview").set_defaults(func=do_stream_list)
    # -- stream get
    get_stream_ap = stream_subs.add_parser('get', help="dumps stream configuration json to stdout")
    get_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    get_stream_ap.set_defaults(func=do_stream_get)
    # -- stream set
    set_stream_ap = stream_subs.add_parser('set', help="overwrites stream configuration with json input from stdin")
    set_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    set_stream_ap.set_defaults(func=do_placeholder)
    # -- stream new
    stream_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new stream based on the json input from stdin"
        ).set_defaults(func=do_placeholder)
    # -- stream del
    del_stream_ap = stream_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified stream")
    del_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    del_stream_ap.set_defaults(func=do_placeholder)
    # -- stream play
    play_stream_ap = stream_subs.add_parser('play', aliases=['pl'], help="plays the specified stream")
    play_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    play_stream_ap.set_defaults(func=do_placeholder)
    # -- stream pause
    pause_stream_ap = stream_subs.add_parser('pause', aliases=['ps'], help="pauses the specified stream")
    pause_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    pause_stream_ap.set_defaults(func=do_placeholder)
    # -- stream stop
    stop_stream_ap = stream_subs.add_parser('stop', aliases=['st'], help="stops the specified stream")
    stop_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    stop_stream_ap.set_defaults(func=do_placeholder)
    # -- stream next
    next_stream_ap = stream_subs.add_parser('next', aliases=['fwd', '»'], help="forwards the specified stream to next item")
    next_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    next_stream_ap.set_defaults(func=do_placeholder)
    # -- stream prev
    prev_stream_ap = stream_subs.add_parser(
        'previous', aliases=['prev', 'back', 'bwd', '«'],
        help="reverses the specified stream back to the previous item")
    prev_stream_ap.add_argument("streamid", action='store', type=int, metavar="ID", help="identifier of the stream")
    prev_stream_ap.set_defaults(func=do_placeholder)

    # details of the announce handling branch
    topic_announce_ap.add_argument("media_url", metavar="URL", action='store', help="URL to playable audio file")
    topic_announce_ap.add_argument(
        "vol_f", metavar="volume%", nargs='*',
        action='store', help="float between 0 and 1 indicating volume")
    topic_announce_ap.set_defaults(func=do_placeholder)

    # details of the preset handling branch
    preset_subs = topic_preset_ap.add_subparsers(title='actions to perform', required=True, metavar="ACTION",)
    # -- preset list
    preset_subs.add_parser('list', aliases=['ls'], help="list presets overview").set_defaults(func=do_preset_list)
    # -- preset get
    get_preset_ap = preset_subs.add_parser('get', help="dumps preset configuration json to stdout")
    get_preset_ap.add_argument("presetid", action='store', type=int, metavar="ID", help="identifier of the preset")
    get_preset_ap.set_defaults(func=do_preset_get)
    # -- preset set
    set_preset_ap = preset_subs.add_parser('set', help="overwrites preset configuration with json input from stdin")
    set_preset_ap.add_argument("presetid", action='store', type=int, metavar="ID", help="identifier of the preset")
    set_preset_ap.set_defaults(func=do_placeholder)
    # -- preset new
    preset_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new preset based on the json input from stdin"
        ).set_defaults(func=do_placeholder)
    # -- preset del
    del_preset_ap = preset_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified preset")
    del_preset_ap.add_argument("presetid", action='store', type=int, metavar="ID", help="identifier of the preset")
    del_preset_ap.set_defaults(func=do_placeholder)
    return parent_ap


def yaml_load_file(file):
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


def make_amplipi(args: Namespace) -> AmpliPi:
    endpoint = args.amplipi
    timeout = args.timeout
    return AmpliPi(endpoint, timeout=timeout)


def main():
    exitcode = 0  # assuming all will be well
    load_dotenv()
    ap = get_arg_parser()
    args = ap.parse_args()
    enable_logging(logconf=args.logconf)
    amplipi = make_amplipi(args)

    # setup async wait construct for main routines
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        # trigger the actual called action-function (async) and wait for it
        loop.run_until_complete(args.func(args, amplipi))
    except (AssertionError, APIError) as e:
        log.error(e)
        exitcode = 1
    except Exception as e:
        log.exception(e)
        print(e)
        exitcode = 1
    finally:
        loop.run_until_complete(amplipi.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        sys.exit(exitcode)


if __name__ == '__main__':
    main()
