from http.client import responses
from json.decoder import JSONDecodeError
from typing import Optional
from urllib.parse import urljoin

import requests
import sys
from aiohttp import ClientSession, ClientResponse
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from .error import AccessDeniedError, APIError, AmpliPiUnreachableError


def headers_or_default(headers=None):
    """Create default headers for API requests or use provided headers.

    Args:
        headers (dict, optional): Custom headers to use. Defaults to None.

    Returns:
        dict: Headers dictionary with content type and user agent set if none provided.
    """
    if headers is None:
        return {
            'Accept-Content': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'pyamplipi-client'
        }
    return headers


class Client:
    """Async HTTP client for interacting with the AmpliPi streaming device API.

    This client handles all HTTP communication with an AmpliPi device, including
    authentication, request formatting, and error handling.

    Attributes:
        _endpoint (str): Base URL of the AmpliPi API
        _timeout (int): Default timeout for API requests in seconds
        _http_session (ClientSession): aiohttp session for making requests

    Args:
        endpoint (str): Base URL of the AmpliPi device API
        timeout (int, optional): Request timeout in seconds. Defaults to 10.
        http_session (ClientSession, optional): Existing aiohttp session to use. Defaults to None.
        verify_ssl (bool, optional): Whether to verify SSL certificates. Defaults to False.
        disable_insecure_warning (bool, optional): Whether to disable SSL warning messages. Defaults to True.

    Example:
        ```python
        client = Client("http://amplipi.local")
        response = await client.get("status")
        await client.close()
        ```
    """

    def __init__(
            self,
            endpoint: str,
            timeout: int = 10,
            http_session: Optional[ClientSession] = None,
            verify_ssl: bool = False,
            disable_insecure_warning: bool = True,
    ) -> None:
        if disable_insecure_warning:
            disable_warnings(InsecureRequestWarning)

        self._endpoint = self._parse_endpoint(endpoint)
        self._timeout = timeout
        self._http_session = http_session if http_session else ClientSession()
        self._http_session.verify = verify_ssl

    def _timeout_or_self(self, timeout: Optional[int] = None) -> int:
        """Get the appropriate timeout value.

        Args:
            timeout (int, optional): Specific timeout value to use. Defaults to None.

        Returns:
            int: The provided timeout value or the default client timeout.
        """
        return timeout if timeout is not None else self._timeout

    @staticmethod
    def _parse_endpoint(endpoint: str) -> str:
        """Ensure the API endpoint URL is properly formatted.

        Adds '/api/' to the endpoint URL if not already present.

        Args:
            endpoint (str): Base URL of the AmpliPi device

        Returns:
            str: Properly formatted API endpoint URL
        """
        if not endpoint.endswith("api") and not endpoint.endswith("/"):
            endpoint += "/api/"
        elif endpoint.endswith("api"):
            endpoint += "/"
        elif endpoint.endswith("/") and not endpoint.endswith("api/"):
            endpoint += "api/"

        return endpoint

    @staticmethod
    async def _handle_error(response: ClientResponse) -> None:
        """Handle error responses from the API.

        Args:
            response (ClientResponse): The error response from the API

        Raises:
            APIError: For general API errors including 404
            AccessDeniedError: For authentication/authorization errors (401/403)
        """
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

    async def _write_response(self, response: ClientResponse, outfile: Optional[str] = None) -> None:
        """Write API response to a file or stdout.

        Args:
            response (ClientResponse): The API response to write
            outfile (str, optional): Path to output file. If None, writes to stdout. Defaults to None.

        Raises:
            APIError: If response indicates an error or if binary content would be written to stdout
        """
        if response.status >= 400:
            await self._handle_error(response)

        if outfile:
            with open(outfile, 'wb') as out:
                out.write(await response.read())
        else:
            ctype = response.headers.get('content-type')
            if ctype is not None and (ctype.startswith('text/') or ctype in ('application/json', )):
                print("we think it is ok to write ", ctype)
                sys.stdout.write((await response.read()).decode('utf-8'))
            else:
                raise APIError(f"No output file provided. Content of type {ctype} will not be written to terminal/stdout")

    async def _process_response(self, response: ClientResponse) -> dict:
        """Process JSON response from the API.

        Args:
            response (ClientResponse): The API response to process

        Returns:
            dict: Parsed JSON response data

        Raises:
            APIError: If response indicates an error or JSON parsing fails
        """
        if response.status >= 400:
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

    def url(self, path: str) -> str:
        """Build a full API URL from a path.

        Args:
            path (str): API endpoint path

        Returns:
            str: Complete API URL
        """
        return urljoin(self._endpoint, path)

    async def delete(self, path: str, body=None, headers=None) -> dict:
        """Send DELETE request to the API.

        Args:
            path (str): API endpoint path
            body (Any, optional): Request body data. Defaults to None.
            headers (dict, optional): Custom request headers. Defaults to None.

        Returns:
            dict: Parsed JSON response data

        Raises:
            AmpliPiUnreachableError: If connection fails
        """
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
        """Send PATCH request to the API.

        Args:
            path (str): API endpoint path
            body (Any, optional): Request body data. Defaults to None.
            headers (dict, optional): Custom request headers. Defaults to None.

        Returns:
            dict: Parsed JSON response data

        Raises:
            AmpliPiUnreachableError: If connection fails
        """
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

    async def post(self, path: str, body=None, headers=None, timeout=None) -> dict:
        """Send POST request to the API.

        Args:
            path (str): API endpoint path
            body (Any, optional): Request body data. Defaults to None.
            headers (dict, optional): Custom request headers. Defaults to None.
            timeout (int, optional): Request timeout override. Defaults to None.

        Returns:
            dict: Parsed JSON response data

        Raises:
            AmpliPiUnreachableError: If connection fails
        """
        try:
            async with self._http_session.post(
                    url=self.url(path),
                    data=body,
                    timeout=self._timeout_or_self(timeout),
                    headers=headers_or_default(headers),
            ) as response:
                return await self._process_response(response)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
        ) as e:
            raise AmpliPiUnreachableError(e)

    async def get(self, path: str, headers=None, expect_json: bool = True, outfile: Optional[str] = None) -> dict:
        """Send GET request to the API.

        Args:
            path (str): API endpoint path
            headers (dict, optional): Custom request headers. Defaults to None.
            expect_json (bool, optional): Whether to expect and parse JSON response. Defaults to True.
            outfile (str, optional): Path to save response content. Defaults to None.

        Returns:
            dict: Parsed JSON response data if expect_json=True, empty dict otherwise

        Raises:
            AmpliPiUnreachableError: If connection fails
        """
        try:
            async with self._http_session.get(
                    url=self.url(path),
                    timeout=self._timeout,
                    headers=headers_or_default(headers),
            ) as response:
                if expect_json:
                    return await self._process_response(response)
                await self._write_response(response, outfile)
                return {}
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
        ) as e:
            raise AmpliPiUnreachableError(e)

    async def close(self):
        """Close the HTTP session.

        This should be called when the client is no longer needed to clean up resources.
        Required for testing to avoid warnings about unclosed resources.
        """
        await self._http_session.close()
