import logging
import logging.config
import asyncio
import sys
import os
import json
import yaml
import datetime
from dotenv import load_dotenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, Action
from typing import List, Callable
from pydantic import BaseModel
from pydantic.fields import ModelField
from tabulate import tabulate
from textwrap import indent
import validators
from .models import Status, Info, Source, Zone, Group, Stream, Preset, Announcement
from .amplipi import AmpliPi
from .error import APIError


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
    """ Prints out comprehensive status information
    """
    log.debug("status.list")
    status: Status = await amplipi.get_status()
    list_status(status)


async def do_status_get(args: Namespace, amplipi: AmpliPi):
    """ Gets Status json represenatation
    """
    log.debug("status.get")
    status: Status = await amplipi.get_status()
    print(status.json(**json_ser_kwargs))

# async def do_status_set(args: Namespace, amplipi: AmpliPi):


async def do_source_list(args: Namespace, amplipi: AmpliPi):
    """ Prints out comprehensive listing of sources
    """
    log.debug("source.list")
    sources: List[Source] = await amplipi.get_sources()
    list_sources(sources)


async def do_source_get(args: Namespace, amplipi: AmpliPi):
    """ Gets Sources json represenatation by source_id
    """
    log.debug(f"source.get({args.sourceid})")
    assert 0 <= args.sourceid <= 3, "source id must be in range 0..3"
    source: Source = await amplipi.get_source(args.sourceid)
    print(source.json(**json_ser_kwargs))

# async def do_source_set(args: Namespace, amplipi: AmpliPi):


async def do_zone_list(args: Namespace, amplipi: AmpliPi):
    """ Prints out comprehensive listing of zones
    """
    log.debug("zone.list")
    zones: List[Zone] = await amplipi.get_zones()
    list_zones(zones)


async def do_zone_get(args: Namespace, amplipi: AmpliPi):
    """ Gets Zone json represenatation by zone_id
    """
    log.debug(f"zone.get({args.zoneid})")
    assert 0 <= args.zoneid <= 35, "zone id must be in range 0..35"
    zone: Zone = await amplipi.get_zone(args.zoneid)
    print(zone.json(**json_ser_kwargs))

# async def do_zone_set(args: Namespace, amplipi: AmpliPi):


async def do_group_list(args: Namespace, amplipi: AmpliPi):
    """ Prints out comprehensive listing of groups
    """
    log.debug("group.list")
    groups: List[Group] = await amplipi.get_groups()
    list_groups(groups)


async def do_group_get(args: Namespace, amplipi: AmpliPi):
    """ Gets Group json represenatation by group_id
    """
    log.debug(f"group.get({args.groupid})")
    assert 0 <= args.groupid, "group id must be > 0"
    group: Group = await amplipi.get_group(args.groupid)
    print(group.json(**json_ser_kwargs))

# async def do_group_set(args: Namespace, amplipi: AmpliPi):
# async def do_group_load(args: Namespace, amplipi: AmpliPi):
# async def do_group_new(args: Namespace, amplipi: AmpliPi):
# async def do_group_del(args: Namespace, amplipi: AmpliPi):


async def do_stream_list(args: Namespace, amplipi: AmpliPi):
    """ Prints out comprehensive listing of streams
    """
    log.debug("stream.list")
    streams: List[Stream] = await amplipi.get_streams()
    list_streams(streams)


async def do_stream_get(args: Namespace, amplipi: AmpliPi):
    """ Gets Stream json represenatation by stream_id
    """
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
    """ Prints out comprehensive listing of presets
    """
    log.debug("preset.list")
    preset: List[Preset] = await amplipi.get_presets()
    list_presets(preset)


async def do_preset_get(args: Namespace, amplipi: AmpliPi):
    """ Gets Preset json representation by preset_id
    """
    log.debug(f"preset.get({args.presetid})")
    assert 0 <= args.presetid, "preset id must be > 0"
    preset: Preset = await amplipi.get_preset(args.presetid)
    print(preset.json(**json_ser_kwargs))


# async def do_preset_set(args: Namespace, amplipi: AmpliPi):
# async def do_preset_new(args: Namespace, amplipi: AmpliPi):
# async def do_preset_del(args: Namespace, amplipi: AmpliPi):


async def do_announce(args: Namespace, amplipi: AmpliPi):
    """ Plays announcement
    """
    def validate(input: dict):
        log.debug(f"validating announcement kwargs: {input}")
        # TODO see github-issue #7 -- since v0.1.8 less variables are required
        # source_id=3 and vol_f should become optional
        input['vol_f'] = input.get('vol_f', 0.5)
        input['source_id'] = input.get('source_id', 3)
        assert validators.url(input['media']), "media_url must be a valid URL"
        assert 0.0 <= input['vol_f'] <= 1.0, "vol_f must be in range 0.0..1.0"

    log.debug(f"announce(input={args.input if args.input is not None else '«stdin»'})")
    announcement: Announcement = instantiate_model(Announcement, args.input, validate)
    await amplipi.announce(announcement)   # returns Status object which we ignore


def instantiate_model(model: BaseModel, input: dict, validate: Callable):
    """ Instatiates the passed BaseModel based on:
      (1) either the passed input dict (if not None) merged with env var defaults
      (2) a json representation read from stdin
    """
    if input is not None:
        input = merge_model_kwargs(model, input)
        if validate is not None:
            validate(input)
        return model(**input)
    # else read the object from stdin (json)
    return model.parse_obj(json.loads(sys.stdin.read()))


def merge_model_kwargs(model: BaseModel, input: dict):
    """ Builds the kwargs needed to construct the passed BaseModel by merging the passed input dict
    with possible available environment variables with key following this pattern:
        "AMPLIPI_" + «name of BaseModel» + "_" + «name of field in BaseModel» (in all caps)
    """
    def envvar(name):
        envkey: str = f"AMPLIPI_{model.__name__}_{name}".upper()
        return os.getenv(envkey)
    kwargs = dict()
    for name, modelfield in model.__fields__.items():
        value_str: str = input.get(name, envvar(name))
        if value_str is not None and type(value_str) == str and len(value_str) > 0:
            kwargs[name] = parse_valuestr(value_str, modelfield)
    return kwargs


def parse_valuestr(val_str: str, modelfield: ModelField):
    """ Uses the pydantic defined Modelfield to correctly parse CLI passed string-values to typed values
    Supports simple types and lists of them
    """
    convertor = modelfield.type_
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


def add_id_argument(ap, model):
    """ Adds the input argument in a consistent way
    """
    name = model.__name__.lower()
    ap.add_argument(f"{name}id", action='store', type=int, metavar="ID", help="identifier of the {name}")


def add_input_argument(ap, model):
    """ Adds the --input -i argument in a consistent way
    The argument takes key-value pairs to construct models rather then provide those in json via stdin
    """
    ap.add_argument(
        '--input', '-i',
        metavar="KEY=VALUE",
        nargs="*",
        help=f"Set any of the fields ({', '.join(model.__fields__.keys())}) to the {model.__name__} object inline."
        " (do not put spaces before or after the = sign). "
        " Use double quotes to let values have spaces."
        ' foo="this is a sentence".'
        " Using this avoids passing the json representation via stdin.",
        action=ParseDict,
    )


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

    action_supbarser_kwargs = dict(title='actions to perform', required=True, metavar="ACTION",)

    # details of the status handling branch
    status_subs = topic_status_ap.add_subparsers(**action_supbarser_kwargs)
    # -- status list
    status_subs.add_parser('list', aliases=['ls'], help="list status overview").set_defaults(func=do_status_list)
    # -- status get
    status_subs.add_parser('get', help="dumps status json to stdout").set_defaults(func=do_status_get)
    # -- status set
    status_subs.add_parser('set', help="overwrites status json with input from stdin").set_defaults(func=do_placeholder)

    # details of the source handling branch
    source_subs = topic_source_ap.add_subparsers(**action_supbarser_kwargs)
    # -- source list
    source_subs.add_parser('list', aliases=['ls'], help="list sources overview").set_defaults(func=do_source_list)
    # -- source get
    get_source_ap = source_subs.add_parser('get', help="dumps source configuration json to stdout")
    add_id_argument(get_source_ap, Source)
    get_source_ap.set_defaults(func=do_source_get)
    # -- source set
    set_source_ap = source_subs.add_parser('set', help="overwrites source configuration with json input from stdin")
    add_id_argument(set_source_ap, Source)
    set_source_ap.set_defaults(func=do_placeholder)

    # details of the zone handling branch
    zone_subs = topic_zone_ap.add_subparsers(**action_supbarser_kwargs)
    # -- zone list
    zone_subs.add_parser('list', aliases=['ls'], help="list zones overview").set_defaults(func=do_zone_list)
    # -- zone get
    get_zone_ap = zone_subs.add_parser('get', help="dumps zone configuration json to stdout")
    add_id_argument(get_zone_ap, Zone)
    get_zone_ap.set_defaults(func=do_zone_get)
    # -- zone set
    set_zone_ap = zone_subs.add_parser('set', help="overwrites zone configuration with json input from stdin")
    add_id_argument(set_zone_ap, Zone)
    set_zone_ap.set_defaults(func=do_placeholder)

    # details of the group handling branch
    group_subs = topic_group_ap.add_subparsers(**action_supbarser_kwargs)
    # -- group list
    group_subs.add_parser('list', aliases=['ls'], help="list groups overview").set_defaults(func=do_group_list)
    # -- group get
    get_group_ap = group_subs.add_parser('get', help="dumps group configuration json to stdout")
    add_id_argument(get_group_ap, Group)
    get_group_ap.set_defaults(func=do_group_get)
    # -- group set
    set_group_ap = group_subs.add_parser('set', help="overwrites group configuration with json input from stdin")
    add_id_argument(set_group_ap, Group)
    set_group_ap.set_defaults(func=do_placeholder)
    # -- group load
    load_group_ap = group_subs.add_parser('load', help="overwrites group configuration with json input from stdin")
    add_id_argument(load_group_ap, Group)
    load_group_ap.set_defaults(func=do_placeholder)
    # -- group new
    group_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new group based on the json input from stdin"
        ).set_defaults(func=do_placeholder)
    # -- group del
    del_group_ap = group_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified group")
    add_id_argument(del_group_ap, Group)
    del_group_ap.set_defaults(func=do_placeholder)

    # details of the stream handling branch
    stream_subs = topic_stream_ap.add_subparsers(**action_supbarser_kwargs)
    # -- stream list
    stream_subs.add_parser('list', aliases=['ls'], help="list streams overview").set_defaults(func=do_stream_list)
    # -- stream get
    get_stream_ap = stream_subs.add_parser('get', help="dumps stream configuration json to stdout")
    add_id_argument(get_stream_ap, Stream)
    get_stream_ap.set_defaults(func=do_stream_get)
    # -- stream set
    set_stream_ap = stream_subs.add_parser('set', help="overwrites stream configuration with json input from stdin")
    add_id_argument(set_stream_ap, Stream)
    set_stream_ap.set_defaults(func=do_placeholder)
    # -- stream new
    stream_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new stream based on the json input from stdin"
        ).set_defaults(func=do_placeholder)
    # -- stream del
    del_stream_ap = stream_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified stream")
    add_id_argument(del_stream_ap, Stream)
    del_stream_ap.set_defaults(func=do_placeholder)
    # -- stream play
    play_stream_ap = stream_subs.add_parser('play', aliases=['pl'], help="plays the specified stream")
    add_id_argument(play_stream_ap, Stream)
    play_stream_ap.set_defaults(func=do_placeholder)
    # -- stream pause
    pause_stream_ap = stream_subs.add_parser('pause', aliases=['ps'], help="pauses the specified stream")
    add_id_argument(pause_stream_ap, Stream)
    pause_stream_ap.set_defaults(func=do_placeholder)
    # -- stream stop
    stop_stream_ap = stream_subs.add_parser('stop', aliases=['st'], help="stops the specified stream")
    add_id_argument(stop_stream_ap, Stream)
    stop_stream_ap.set_defaults(func=do_placeholder)
    # -- stream next
    next_stream_ap = stream_subs.add_parser('next', aliases=['fwd', '»'], help="forwards the specified stream to next item")
    add_id_argument(next_stream_ap, Stream)
    next_stream_ap.set_defaults(func=do_placeholder)
    # -- stream prev
    prev_stream_ap = stream_subs.add_parser(
        'previous', aliases=['prev', 'back', 'bwd', '«'],
        help="reverses the specified stream back to the previous item")
    add_id_argument(prev_stream_ap, Stream)
    prev_stream_ap.set_defaults(func=do_placeholder)

    # details of the preset handling branch
    preset_subs = topic_preset_ap.add_subparsers(**action_supbarser_kwargs)
    # -- preset list
    preset_subs.add_parser('list', aliases=['ls'], help="list presets overview").set_defaults(func=do_preset_list)
    # -- preset get
    get_preset_ap = preset_subs.add_parser('get', help="dumps preset configuration json to stdout")
    add_id_argument(get_preset_ap, Preset)
    get_preset_ap.set_defaults(func=do_preset_get)
    # -- preset set
    set_preset_ap = preset_subs.add_parser('set', help="overwrites preset configuration with json input from stdin")
    add_id_argument(set_preset_ap, Preset)
    set_preset_ap.set_defaults(func=do_placeholder)
    # -- preset new
    preset_subs.add_parser(
            'new', aliases=['make', 'create'],
            help="create a new preset based on the json input from stdin"
        ).set_defaults(func=do_placeholder)
    # -- preset del
    del_preset_ap = preset_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified preset")
    add_id_argument(del_preset_ap, Preset)
    del_preset_ap.set_defaults(func=do_placeholder)

    # details of the announce handling branch
    add_input_argument(topic_announce_ap, Announcement)
    topic_announce_ap.set_defaults(func=do_announce)

    return parent_ap


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


def make_amplipi(args: Namespace) -> AmpliPi:
    """ Constructs the amplipi client
    """
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
