import logging
import asyncio
import sys
import os
import yaml
from dotenv import load_dotenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from pyamplipi.models import Status, Announcement
from pyamplipi.amplipi import AmpliPi


log = logging.getLogger(__name__)


async def do_placeholder(args: Namespace, amplipi: AmpliPi):
    log.warning(f"todo handle command args --> \n  args = {args}\n  ammplipi = {amplipi}")


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
        type=str,
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
    status_subs = topic_status_ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="ACTION",
    )
    # -- status list
    status_subs.add_parser('list', aliases=['ls'], help="list status overview").set_defaults(func=do_placeholder)
    # -- status get
    status_subs.add_parser('get', help="dumps status json to stdout").set_defaults(func=do_placeholder)
    # -- status set
    status_subs.add_parser('set', help="overwrites status json with input from stdin").set_defaults(func=do_placeholder)

    # details of the source handling branch
    source_subs = topic_source_ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="ACTION",
    )
    # -- source list
    source_subs.add_parser('list', aliases=['ls'], help="list sources overview").set_defaults(func=do_placeholder)
    # -- source get
    get_source_ap = source_subs.add_parser('get', help="dumps source configuration json to stdout")
    get_source_ap.add_argument("sourceid", action='store', metavar="ID", help="identifier of the source, or '*' for all")
    get_source_ap.set_defaults(func=do_placeholder)
    # -- source set
    set_source_ap = source_subs.add_parser('set', help="overwrites source configuration with json input from stdin")
    set_source_ap.add_argument("sourceid", action='store', metavar="ID", help="identifier of the source")
    set_source_ap.set_defaults(func=do_placeholder)

    # details of the zone handling branch
    zone_subs = topic_zone_ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="ACTION",
    )
    # -- zone list
    zone_subs.add_parser('list', aliases=['ls'], help="list zones overview").set_defaults(func=do_placeholder)
    # -- zone get
    get_zone_ap = zone_subs.add_parser('get', help="dumps zone configuration json to stdout")
    get_zone_ap.add_argument("zoneid", action='store', metavar="ID", help="identifier of the zone, or '*' for all")
    get_zone_ap.set_defaults(func=do_placeholder)
    # -- zone set
    set_zone_ap = zone_subs.add_parser('set', help="overwrites zone configuration with json input from stdin")
    set_zone_ap.add_argument("zoneid", action='store', metavar="ID", help="identifier of the zone")
    set_zone_ap.set_defaults(func=do_placeholder)

    # details of the group handling branch
    group_subs = topic_group_ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="ACTION",
    )
    # -- group list
    group_subs.add_parser('list', aliases=['ls'], help="list groups overview").set_defaults(func=do_placeholder)
    # -- group get
    get_group_ap = group_subs.add_parser('get', help="dumps group configuration json to stdout")
    get_group_ap.add_argument("groupid", action='store', metavar="ID", help="identifier of the group, or '*' for all")
    get_group_ap.set_defaults(func=do_placeholder)
    # -- group set
    set_group_ap = group_subs.add_parser('set', help="overwrites group configuration with json input from stdin")
    set_group_ap.add_argument("groupid", action='store', metavar="ID", help="identifier of the group")
    set_group_ap.set_defaults(func=do_placeholder)
    # -- group load
    load_group_ap = group_subs.add_parser('load', help="overwrites group configuration with json input from stdin")
    load_group_ap.add_argument("groupid", action='store', metavar="ID", help="identifier of the group")
    load_group_ap.set_defaults(func=do_placeholder)
    # -- group new
    group_subs.add_parser('new', aliases=['make', 'create'], help="create a new group based on the json input from stdin").set_defaults(func=do_placeholder)
    # -- group del
    del_group_ap = group_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified group")
    del_group_ap.add_argument("groupid", action='store', metavar="ID", help="identifier of the group")
    del_group_ap.set_defaults(func=do_placeholder)

    # details of the stream handling branch
    stream_subs = topic_stream_ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="ACTION",
    )
    # -- stream list
    stream_subs.add_parser('list', aliases=['ls'], help="list streams overview").set_defaults(func=do_placeholder)
    # -- stream get
    get_stream_ap = stream_subs.add_parser('get', help="dumps stream configuration json to stdout")
    get_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream, or '*' for all")
    get_stream_ap.set_defaults(func=do_placeholder)
    # -- stream set
    set_stream_ap = stream_subs.add_parser('set', help="overwrites stream configuration with json input from stdin")
    set_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    set_stream_ap.set_defaults(func=do_placeholder)
    # -- stream new
    stream_subs.add_parser('new', aliases=['make', 'create'], help="create a new stream based on the json input from stdin").set_defaults(func=do_placeholder)
    # -- stream del
    del_stream_ap = stream_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified stream")
    del_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    del_stream_ap.set_defaults(func=do_placeholder)
    # -- stream play
    play_stream_ap = stream_subs.add_parser('play', aliases=['pl'], help="plays the specified stream")
    play_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    play_stream_ap.set_defaults(func=do_placeholder)
    # -- stream pause
    pause_stream_ap = stream_subs.add_parser('pause', aliases=['ps'], help="pauses the specified stream")
    pause_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    pause_stream_ap.set_defaults(func=do_placeholder)
    # -- stream stop
    stop_stream_ap = stream_subs.add_parser('stop', aliases=['st'], help="stops the specified stream")
    stop_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    stop_stream_ap.set_defaults(func=do_placeholder)
    # -- stream next
    next_stream_ap = stream_subs.add_parser('next', aliases=['fwd', '»'], help="forwards the specified stream to next item")
    next_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    next_stream_ap.set_defaults(func=do_placeholder)
    # -- stream prev
    prev_stream_ap = stream_subs.add_parser('previous', aliases=['prev', 'back', 'bwd', '«'], help="reverses the specified stream back to the previous item")
    prev_stream_ap.add_argument("streamid", action='store', metavar="ID", help="identifier of the stream")
    prev_stream_ap.set_defaults(func=do_placeholder)

    # details of the announce handling branch
    topic_announce_ap.add_argument("media_url", metavar="URL", action='store', help="URL to playable audio file")
    topic_announce_ap.add_argument("vol_f", metavar="volume%", nargs='*', action='store', help="float between 0 and 1 indicating volume")
    topic_announce_ap.set_defaults(func=do_placeholder)

    # details of the preset handling branch
    preset_subs = topic_preset_ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="ACTION",
    )
    # -- preset list
    preset_subs.add_parser('list', aliases=['ls'], help="list presets overview").set_defaults(func=do_placeholder)
    # -- preset get
    get_preset_ap = preset_subs.add_parser('get', help="dumps preset configuration json to stdout")
    get_preset_ap.add_argument("presetid", action='store', metavar="ID", help="identifier of the preset, or '*' for all")
    get_preset_ap.set_defaults(func=do_placeholder)
    # -- preset set
    set_preset_ap = preset_subs.add_parser('set', help="overwrites preset configuration with json input from stdin")
    set_preset_ap.add_argument("presetid", action='store', metavar="ID", help="identifier of the preset")
    set_preset_ap.set_defaults(func=do_placeholder)
    # -- preset new
    preset_subs.add_parser('new', aliases=['make', 'create'], help="create a new preset based on the json input from stdin").set_defaults(func=do_placeholder)
    # -- preset del
    del_preset_ap = preset_subs.add_parser('delete', aliases=['del', 'rm'], help="deletes the specified preset")
    del_preset_ap.add_argument("presetid", action='store', metavar="ID", help="identifier of the preset")
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
    loop = asyncio.new_event_loop()
    try:
        # trigger the actual called action-function (async) and wait for it
        loop.run_until_complete(args.func(args, amplipi))
    except Exception as e:
        log.exception(e)
        exitcode = 1
    finally:
        loop.run_until_complete(amplipi.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        sys.exit(exitcode)


if __name__ == '__main__':
    main()
