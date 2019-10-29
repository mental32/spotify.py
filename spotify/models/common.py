import json
import time
from pathlib import Path
from typing import Optional, Any, Dict, Union

_CACHE_FILE_FIELDS = {"access_token", "expires_at", "refresh_token"}
_CACHE_FILE_ERR = "Bad cache file! Missing the following fields: {}"


class Image:
    """An object representing a Spotify image resource.

    Attributes
    ----------
    height : :class:`str`
        The height of the image.
    width : :class:`str`
        The width of the image.
    url : :class:`str`
        The URL of the image.
    """

    __slots__ = ("height", "width", "url")

    def __init__(self, *, height: str, width: str, url: str):
        self.height = height
        self.width = width
        self.url = url

    def __repr__(self):
        return f"<spotify.Image: {self.url!r} (width: {self.width!r}, height: {self.height!r})>"

    def __eq__(self, other):
        return type(self) is type(other) and self.url == other.url


class Context:
    """A Spotify Context.

    Attributes
    ----------
    type : str
        The object type, e.g. “artist”, “playlist”, “album”.
    href : str
        A link to the Web API endpoint providing full details of the track.
    external_urls : str
        External URLs for this context.
    uri : str
        The Spotify URI for the context.
    """

    __slots__ = ("external_urls", "type", "href", "uri")

    def __init__(self, data):
        self.external_urls = data.get("external_urls")
        self.type = data.get("type")

        self.href = data.get("href")
        self.uri = data.get("uri")

    def __repr__(self):
        return f"<spotify.Context: {self.uri!r}>"

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri


class Device:
    """A Spotify Users device.

    Attributes
    ----------
    id : str
        The device ID
    name : int
        The name of the device.
    type : str
        A Device type, such as “Computer”, “Smartphone” or “Speaker”.
    volume : int
        The current volume in percent. This may be null.
    is_active : bool
        if this device is the currently active device.
    is_restricted : bool
        Whether controlling this device is restricted.
        At present if this is “true” then no Web API commands will be accepted by this device.
    is_private_session : bool
        If this device is currently in a private session.
    """

    __slots__ = (
        "id",
        "name",
        "type",
        "volume",
        "is_active",
        "is_restricted",
        "is_private_session",
    )

    def __init__(self, data):
        self.id = data.get("id")  # pylint: disable=invalid-name
        self.name = data.get("name")
        self.type = data.get("type")

        self.volume = data.get("volume_percent")

        self.is_active = data.get("is_active")
        self.is_restricted = data.get("is_restricted")
        self.is_private_session = data.get("is_private_session")

    def __eq__(self, other):
        return type(self) is type(other) and self.id == other.id

    def __repr__(self):
        return f"<spotify.Device: {(self.name or self.id)!r}>"

    def __str__(self):
        return self.id


class TokenInfo:
    """An object holding a users authentication tokens and corresponding information.

    Attributes
    ----------
    access_token : :class:`str`
        The authentication token
    expires_in : :class:`int`
        Time in seconds until the authentication token expires
    refresh_token : Optional[:class:`str`]
        Refresh token used to re-fetch new access tokens once they expire
    token_type : Optional[:class:`str`]
        Type of the token, typically 'Bearer'
    scope : Optional[:class:`str`]
        Oauth2 scopes the access token is valid for. Space separated list of individual scopes.
    expires_at : :class:`float`
        Time at which the access token expires as a unix timestamp in seconds.
        Computed from expires_in and the current time at object instantiation.
    cache_file: Optional[:class:`Path`]
        File path where to cache the token information.
    """

    __slots__ = (
        "access_token",
        "expires_in",
        "refresh_token",
        "token_type",
        "scope",
        "expires_at",
        "cache_file",
    )

    def __init__(
        self,
        access_token: str,
        expires_in: int,
        refresh_token: Optional[str] = None,
        token_type: Optional[str] = None,
        scope: Optional[str] = None,
        expires_at: Optional[float] = None,
        cache_file: Optional[Union[Path, str]] = None,
    ):
        self.access_token = access_token
        self.expires_in = expires_in
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.scope = scope
        self.expires_at = expires_at or time.time() + self.expires_in

        if isinstance(cache_file, str):
            cache_file = Path(cache_file)
        self.cache_file = cache_file

    @property
    def valid(self) -> bool:
        """Check if the current token is valid,
        i.e. if it has expired.

        Returns
        ----------
        valid : bool
        """
        return self.expires_at > time.time()

    def serialize(self) -> dict:
        """Create a serialized dict that contains
        essential information about the token to
        be used when e.g. caching to a file.

        Returns
        ----------
        serialized : dict
            dict representation of the token information
        """
        return {
            "access_token": self.access_token,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
            "scope": self.scope,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
        }

    @classmethod
    def from_file(cls, file_path: Path):
        """Load token information from a json file.

        Parameters
        ----------
        file_path : :class `Path`
            Path a json file to load token info from.
        """
        data = json.loads(file_path.read_text())

        fields = set(data.keys())

        if not _CACHE_FILE_FIELDS.issubset(fields):
            raise ValueError(
                _CACHE_FILE_ERR.format(_CACHE_FILE_FIELDS.difference(fields).pop())
            )

        return cls(cache_file=file_path, **data)

    def save_to_file(self) -> None:
        """Save token information to cache file as a json file.
        The file must exist for the operation to be successful.
        Will raise FileNotFoundError if the file does not exist.
        """
        if not self.cache_file:
            return

        if not self.cache_file.exists():
            raise FileNotFoundError("Cache file does not exist.")

        self.cache_file.write_text(json.dumps(self.serialize()))
