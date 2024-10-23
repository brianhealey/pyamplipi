from typing import Optional


class AmpliPiError(Exception):
    """Base exception class for all AmpliPi-related errors.

    Args:
        msg (str): Error message describing the error condition
    """
    def __init__(self, msg):
        super().__init__(msg)


class APIError(AmpliPiError):
    """Exception raised when the AmpliPi API returns an error response.

    Args:
        error (str): Error message returned by the API
    """
    def __init__(self, error):
        super().__init__("AmpliPi api error: {}".format(error))


class MissingAttributeError(APIError):
    """Exception raised when an expected attribute is missing from an API response.

    Args:
        response (dict): The API response that is missing the attribute
        attribute (str): Name of the missing attribute
        url (str, optional): URL of the API endpoint that was called. Defaults to None.

    Attributes:
        response (dict): The API response that is missing the attribute
        attribute (str): Name of the missing attribute
        url (Optional[str]): URL of the API endpoint that was called
    """
    def __init__(self, response: dict, attribute: str, url: Optional[str] = None):
        self.response = response
        self.attribute = attribute
        self.url = url

        if url is None:
            super().__init__(
                "The attribute '{}' is expected in the response but is missing.".format(
                    attribute
                )
            )
        else:
            super().__init__(
                "The attribute '{}' is expected in the response for '{}' but is missing.".format(
                    attribute, url
                )
            )


class AmpliPiUnreachableError(AmpliPiError):
    """Exception raised when the AmpliPi device cannot be reached.

    Args:
        reason (Any, optional): The reason for the connection failure. Defaults to None.

    Attributes:
        reason (Any): The underlying cause of the connection failure
    """
    def __init__(self, reason=None):
        msg = "AmpliPi is unreachable"
        self.reason = reason
        if reason is not None:
            msg = "{}: {}".format(msg, reason)
        super().__init__(msg)


class AccessDeniedError(AmpliPiError):
    """Exception raised when access to an AmpliPi resource is denied.

    Args:
        resource (str): The resource that was attempted to be accessed
        error (str, optional): Specific error code returned. Defaults to None.
        message (str, optional): Detailed error message. Defaults to None.

    Attributes:
        resource (str): The resource that was attempted to be accessed
        error (Optional[str]): Specific error code returned
        message (Optional[str]): Detailed error message
    """
    def __init__(self, resource, error=None, message=None):
        self.resource = resource
        self.error = error
        self.message = message
        msg = "Access denied for resource {}".format(resource)
        if error is not None:
            if message is not None:
                msg = "{}: {}: {}".format(msg, error, message)
            else:
                msg = "{}: {}".format(msg, error)
        super().__init__(msg)
