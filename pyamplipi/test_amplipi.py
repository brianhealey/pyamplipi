
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, get_type_hints, Coroutine, Callable
from itertools import product
from unittest.mock import AsyncMock, patch
import asyncio
import pytest
from aiohttp import ClientSession
import yaml
from pyamplipi.amplipi import AmpliPi
from pyamplipi.models import Status, Source, Zone, Group, Stream, Preset, SourceUpdate, ZoneUpdate, \
    GroupUpdate, StreamUpdate, PresetUpdate, Announcement, PlayMedia, Config


@dataclass
class OpenAPIExample:
    """ OpenAPI example with a paired request and response

    Most examples from AmpliPi's OpenAPI specification either have a request or a response, some have both.
    """
    name: str
    request: Optional[Dict[str, Any]]
    response: Optional[Dict[str, Any]]


class OpenAPITestGenerator:
    """ Generates example requests and responses for testing the AmpliPi API using OpenAPI specifications."""

    def __init__(self, spec_paths: List[str]):
        self.model_mapping = {
            'Status': Status,
            'Source': Source,
            'Zone': Zone,
            'Group': Group,
            'Stream': Stream,
            'Preset': Preset,
            'SourceUpdate': SourceUpdate,
            'ZoneUpdate': ZoneUpdate,
            'GroupUpdate': GroupUpdate,
            'StreamUpdate': StreamUpdate,
            'PresetUpdate': PresetUpdate,
            'Announcement': Announcement,
            'PlayMedia': PlayMedia,
            'Config': Config
        }

        self.specs = {}
        for path in spec_paths:
            with open(path, 'r', encoding='utf-8') as f:
                # Extract version from filename
                version = Path(path).stem.split('.yaml')[-1]
                self.specs[version] = yaml.safe_load(f)

    def combine_examples(self, request_examples: Dict[str, Any], response_examples: Dict[str, Any]) -> List[OpenAPIExample]:
        """ Pair response examples with request examples by name or as a fallback using  the default response example."""
        # many of the API examples return a default status example, currently called "Status of Jason's AmpliPi"
        # we pair this response with every request example that doesn't have a matching response
        # the default response is removed as an example unless it is the only one
        #  this avoids making an example that has no matching request
        examples = []
        default_response = None
        if request_examples:
            example_names = set(request_examples.keys())
            if example_names.isdisjoint(response_examples.keys()) and len(response_examples) == 1:
                default_response = response_examples.popitem()[1]['value']
        for named_example in request_examples.keys() | response_examples.keys():
            request_data = request_examples.get(
                named_example, {}).get('value', None)
            response_data = response_examples.get(
                named_example, {}).get('value', default_response)
            examples.append(OpenAPIExample(
                named_example, request_data, response_data))
        return examples

    def get_examples(self, version: str, path: str, method: str) -> List[OpenAPIExample]:
        """Extract example requests and responses for a given API operation"""
        examples = []

        spec = self.specs[version]
        path_obj = spec['paths'][path][method.lower()]
        try:
            response_content = path_obj['responses']['200']['content']['application/json']
        except KeyError:
            response_content = {}
        try:
            request_content = path_obj['requestBody']['content']['application/json']
        except KeyError:
            request_content = {}
        if 'example' in request_content or 'example' in response_content:
            examples.append(OpenAPIExample('default_example', request_content.get(
                'example', None), response_content.get('example', None)))
        if 'examples' in request_content or 'examples' in response_content:
            request_examples = request_content.get('examples', {})
            response_examples = response_content.get('examples', {})
            # a few examples are added as lists, the rest of the code expects dict based examples
            if isinstance(request_examples, list):
                request_examples = {f'example_{i+1}': {'value': example}
                                    for i, example in enumerate(request_examples)}
            if isinstance(response_examples, list):
                response_examples = {f'example_{i+1}': {'value': example}
                                     for i, example in enumerate(response_examples)}
            examples += self.combine_examples(request_examples,
                                              response_examples)
        return examples

    def get_example_params(self, version: str, path: str, method: str) -> List[Dict[str, Any]]:
        """ Get a list of example parameter combinations for a given API operation"""
        spec = self.specs[version]
        path_obj = spec['paths'][path][method.lower()]
        params = path_obj.get('parameters', [])
        example_params = {}
        # grab a list of examples values for each parameter
        for param in params:
            param_name = param['name']
            # attempt to grab example parameters
            if 'examples' in param:
                examples = param['examples']
                example_params[param_name] = [example['value']
                                              for _, example in examples.items() if 'value' in example]

            # fallback to examples from the potentially referenced schema
            elif 'schema' in param:
                # TODO: for now we only have enums without examples
                schema_name = None
                if '$ref' in param['schema']:
                    # lookup the schema
                    schema_name = param['schema']['$ref'].split('/')[-1]
                    schema = self.specs[version]['components']['schemas'][schema_name]
                else:
                    schema = param['schema']
                if 'enum' in schema:
                    example_params[param_name] = schema['enum']
                    if schema_name == 'StreamCommand':
                        filtered_cmds = [cmd for cmd in schema['enum']
                                         if cmd not in excluded_stream_commands]
                        example_params[param_name] = filtered_cmds
                else:
                    # we haven't implemented the rest of this logic yet
                    raise NotImplementedError(
                        f'Handling other schema types: {param}')
        # transform this into a list of potential parameter combinations each combination as a dictionary {param: value}
        # { 'sid' : [1, 2], 'cmd': ['play', 'pause']}
        #  -> [{'sid': 1, 'cmd': 'play'}, {'sid': 1, 'cmd': 'pause'}, {'sid': 2, 'cmd': 'play'}, {'sid': 2, 'cmd': 'pause'}]
        combinations = product(*example_params.values())
        return [dict(zip(example_params.keys(), comb)) for comb in combinations]

    def versions(self) -> List[str]:
        """Retrieve a list of available API versions."""
        return list(self.specs.keys())

    def get_endpoints(self, version: str) -> List[Tuple[str, str]]:
        """Retrieve a list of API endpoints for a given version."""
        spec = self.specs[version]
        return [(path, method) for path, methods in spec['paths'].items() for method in methods.keys()]


async def exec_command(client: AmpliPi, stream_id: int, cmd: str) -> Status:
    """ Convert a cmd parameter to one of the AmpliPi client's methods and execute it."""
    if cmd == 'play':
        return await client.play_stream(stream_id)
    if cmd == 'pause':
        return await client.pause_stream(stream_id)
    if cmd == 'prev':
        return await client.previous_stream(stream_id)
    if cmd == 'next':
        return await client.next_stream(stream_id)
    if cmd == 'stop':
        return await client.stop_stream(stream_id)
    raise ValueError(f'Unsupported command: {cmd}')


def get_client_method(client: AmpliPi, path: str, method: str):
    """ Translate api path/method to the AmpliPi client's method."""
    direct: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {
        '/api': client.get_status,
        '/api/': client.get_status,
        '/api/load': client.load_config,
        '/api/factory_reset': client.factory_reset,
        '/api/reset': client.system_reset,
        '/api/reboot': client.system_reboot,
        '/api/shutdown': client.system_shutdown,
        '/api/info': client.get_info,
    }
    indirect: Dict[str, Dict[str, Callable[..., Coroutine[Any, Any, Any]]]] = {
        '/api/zones': {
            'get': client.get_zones,
            'patch': client.set_zones,
        },
        '/api/zones/{zid}': {
            'get': client.get_zone,
            'patch': client.set_zone,
        },
        '/api/group': {
            'post': client.create_group,
        },
        '/api/groups': {
            'get': client.get_groups,
        },
        '/api/groups/{gid}': {
            'get': client.get_group,
            'patch': client.set_group,
            'delete': client.delete_group,
        },
        '/api/sources': {
            'get': client.get_sources
        },
        '/api/sources/{sid}': {
            'get': client.get_source,
            'patch': client.set_source
        },
        '/api/stream': {
            'post': client.create_stream,
        },
        '/api/streams': {
            'get': client.get_streams,
        },
        '/api/streams/{sid}': {
            'get': client.get_stream,
            'patch': client.set_stream,
            'delete': client.delete_stream,
        },
        '/api/streams/{sid}/{cmd}': {
            # TODO: make this switch which method to call based on the command
            'post': lambda stream_id, cmd: exec_command(client, stream_id, cmd)
        },
        '/api/preset': {
            'post': client.create_preset,
        },
        '/api/presets': {
            'get': client.get_presets,
        },
        '/api/presets/{pid}': {
            'get': client.get_preset,
            'patch': client.set_preset,
            'delete': client.delete_preset,
        },
        '/api/presets/{pid}/load': {
            'post': client.load_preset,
        },
        '/api/announce': {
            'post': client.announce,
        },
        '/api/play': {
            'post': client.play_media
        }
    }

    if path in direct:
        return direct[path]
    if path in indirect and method in indirect[path]:
        return indirect[path][method]
    raise ValueError(f"Unsupported API endpoint: {path} ({method.upper()})")


async def run_example_test(client: AmpliPi, path: str, method: str, example: OpenAPIExample, path_params: dict) -> None:
    """ Run a generated test """
    method = method.lower()
    with patch('pyamplipi.client.Client.' + method, return_value=example.response):
        amplipi_method = get_client_method(client, path, method)
        # TODO: handle parameters of each endpoint, typically there is only one integer parameter in this case
        params = []
        if len(path_params) == 1:
            params = list(path_params.values())
        elif len(path_params) == 2:
            params = [path_params['sid'], path_params['cmd']]
        elif len(path_params) > 2:
            raise ValueError(f"Too many path parameters for endpoint: {path}")
        if example.request:
            try:
                # convert the request to the appropriate model
                # get the function signature to get the parameter hints
                signature = get_type_hints(amplipi_method)
                # get the last parameter in the function signature
                # (the last param in the signature is the return type)
                if list(signature.keys())[-2] == 'timeout':
                    # the request comes before the timeout
                    request_type = list(signature.values())[-3]
                else:
                    request_type = list(signature.values())[-2]
                # convert the request to the appropriate model
                params.append(request_type.model_validate(example.request))
            except AttributeError:
                params.append(example.request)

        await amplipi_method(*params)


# These endpoints are not used by the AmpliPi client
excluded_endpoints = [
    '/debug',
    '/api/sources/{sid}/image/{height}',
    # TODO: Add support for streams/browser'
    '/api/streams/browser/{sid}/play',
    '/api/streams/browser/{sid}/browse',
    '/api/streams/{sid}/{pid}/browse',
]

# These stream commands are not exposed by the AmpliPi client
excluded_stream_commands = [
    # TODO: handle advanced stream commands
    'activate',
    'deactivate',
    'restart',
    # TODO: handle pandora specific commands
    'love',
    'shelve',
    'ban',
]


def async_partial(f, *args):
    """ Like functools.partial but returns a coroutine. Assumes f is a coroutine."""
    async def f2(*args2):
        result = f(*args, *args2)
        if asyncio.iscoroutinefunction(f):
            result = await result
        return result
    return f2


def create_dynamic_tests():
    """ Generated the test set from the OpenAPI specifications"""
    spec_paths = [
        'specs/0.4.5.yaml'
    ]
    test_generator = OpenAPITestGenerator(spec_paths)
    for version in test_generator.versions():
        amplipi_client = AmpliPi(
            "http://localhost", http_session=AsyncMock(spec=ClientSession))
        # cache the version fro the AmpliPi client, to avoid the asynchronous call needed to get the version
        amplipi_client.version = tuple(int(v) for v in version.split('.'))
        for path, method in test_generator.get_endpoints(version):
            if path in excluded_endpoints:
                print(
                    f'Skipping unused endpoint: {path} ({method.upper()}) (version: {version})')
                continue
            try:
                examples = test_generator.get_examples(
                    version, path, method)
                example_params_combinations = test_generator.get_example_params(
                    version, path, method)
            except (KeyError, NotImplementedError):
                print(
                    f'Skipping unsupported endpoint: {path} ({method.upper()}) (version: {version})')
                continue
            for example in examples:
                for example_params in example_params_combinations or [{}]:
                    # Dynamically generate test functions for each example
                    test_path = path.replace('/', '_')
                    for name, val in example_params.items():
                        test_path = test_path.replace(
                            f'{{{name}}}', str(val))
                    example_name = example.name.replace(
                        ' ', '_').replace("'", "").replace(',', '_')
                    test_function_name = f"test_{version.replace('.','_')}_{test_path}_{method}_{example_name}"
                    # Use partial to pass the amplipi_client and iterator variables to the test function
                    test_function = async_partial(
                        run_example_test, amplipi_client, path, method, example, example_params)
                    # use pytest.mark.asyncio to mark the test function as asynchronous
                    test_function = pytest.mark.asyncio(test_function)
                    # Register the test function in the module
                    globals()[test_function_name] = test_function
                    print("Added test:", test_function_name)


create_dynamic_tests()
