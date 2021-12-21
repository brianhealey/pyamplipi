from http.client import responses
from json.decoder import JSONDecodeError
from urllib.parse import urljoin

import requests
from aiohttp import ClientSession, ClientResponse
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from .error import AccessDeniedError, APIError, AmpliPiUnreachableError


def headers_or_default(headers=None):
    if headers is None:
        return {
            'Accept-Content': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'pyamplipi-client'
        }
    return headers


class Client(object):
    def __init__(
            self,
            endpoint: str,
            timeout: int = 10,
            http_session: ClientSession = None,
            verify_ssl: bool = False,
            disable_insecure_warning: bool = True,
    ) -> None:

        if disable_insecure_warning:
            disable_warnings(InsecureRequestWarning)

        self._endpoint = self._parse_endpoint(endpoint)
        self._timeout = timeout
        self._http_session = http_session if http_session else ClientSession()
        self._http_session.verify = verify_ssl

    @staticmethod
    def _parse_endpoint(endpoint: str) -> str:

        if not endpoint.endswith("api") and not endpoint.endswith("/"):
            endpoint += "/api/"
        elif endpoint.endswith("api"):
            endpoint += "/"
        elif endpoint.endswith("/") and not endpoint.endswith("api/"):
            endpoint += "api/"

        return endpoint

    @staticmethod
    async def _handle_error(response: ClientResponse) -> None:
        if response.status == 404:
            raise APIError(
                "The url {} returned error 404".format(response.url)
            )

        if response.status == 401 or response.status == 403:

            try:
                response_json = await response.json()
            except Exception:
                raise AccessDeniedError(response.url)
            else:
                raise AccessDeniedError(
                    response.url,
                    response_json.get("error"),
                    response_json.get("message"),
                )

        body = await response.text()

        if body is not None and len(body) > 0:
            raise APIError(
                "API returned status code '{}: {}' with body: {}".format(
                    response.status,
                    responses.get(response.status),
                    body,
                )
            )
        else:
            raise APIError(
                "API returned status code '{}: {}' ".format(
                    response.status, responses.get(response.status)
                )
            )

    async def _process_response(self, response: ClientResponse) -> dict:

        if response.status >= 400:
            # API returned some sort of error that must be handled
            await self._handle_error(response)

        try:
            response_json = await response.json()
        except JSONDecodeError:
            raise APIError(
                "Error while decoding json of response: {}".format(response.text())
            )

        if response_json is None:
            return {}

        # Newer versions of the powerwall do not return such values anymore
        # Kept for backwards compability or if the API changes again
        if "error" in response_json:
            raise APIError(response_json["error"])

        return response_json

    def url(self, path: str):
        return urljoin(self._endpoint, path)

    async def delete(self, path: str, body=None, headers=None) -> dict:
        try:
            async with self._http_session.delete(
                    url=self.url(path),
                    data=body,
                    timeout=self._timeout,
                    headers=headers_or_default(headers),
            ) as response:
                return await self._process_response(response)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
        ) as e:
            raise AmpliPiUnreachableError(e)

    async def patch(self, path: str, body=None, headers=None) -> dict:
        try:
            async with self._http_session.patch(
                    url=self.url(path),
                    data=body,
                    timeout=self._timeout,
                    headers=headers_or_default(headers),
            ) as response:
                return await self._process_response(response)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
        ) as e:
            raise AmpliPiUnreachableError(e)

    async def post(self, path: str, body=None, headers=None) -> dict:
        try:
            async with self._http_session.post(
                    url=self.url(path),
                    data=body,
                    timeout=self._timeout,
                    headers=headers_or_default(headers),
            ) as response:
                return await self._process_response(response)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
        ) as e:
            raise AmpliPiUnreachableError(e)

    async def get(self, path: str, headers=None) -> dict:
        try:
            async with self._http_session.get(
                    url=self.url(path),
                    timeout=self._timeout,
                    headers=headers_or_default(headers),
            ) as response:
                return await self._process_response(response)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
        ) as e:
            raise AmpliPiUnreachableError(e)

    async def close(self):
        # Close the HTTP Session
        # THis method is required for testing, so python doesn't complain about unclosed resources
        await self._http_session.close()
