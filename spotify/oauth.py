from urllib.parse import quote_plus as quote
from typing import Optional, Dict, Iterable, Union, Set, Callable, Tuple, Any

VALID_SCOPES = (
    # Playlists
    "playlist-read-collaborative"
    "playlist-modify-private"
    "playlist-modify-public"
    "playlist-read-private"
    # Spotify Connect
    "user-modify-playback-state"
    "user-read-currently-playing"
    "user-read-playback-state"
    # Users
    "user-read-private"
    "user-read-email"
    # Library
    "user-library-modify"
    "user-library-read"
    # Follow
    "user-follow-modify"
    "user-follow-read"
    # Listening History
    "user-read-recently-played"
    "user-top-read"
    # Playback
    "streaming"
    "app-remote-control"
)


def set_required_scopes(*scopes: Optional[str]) -> Callable:
    """A decorator that lets you attach metadata to functions.

    Parameters
    ----------
    scopes : :class:`str`
        A series of scopes that are required.

    Returns
    -------
    decorator : :class:`typing.Callable`
        The decorator that sets the scope metadata.
    """

    def decorate(func) -> Callable:
        func.__requires_spotify_scopes__ = tuple(scopes)
        return func

    return decorate


def get_required_scopes(func: Callable[..., Any]) -> Tuple[str, ...]:
    """Get the required scopes for a function.

    Parameters
    ----------
    func : Callable[..., Any]
        The function to inspect.

    Returns
    -------
    scopes : Tuple[:class:`str`, ...]
        A tuple of scopes required for a call to succeed.
    """
    if not hasattr(func, "__requires_spotify_scopes__"):
        raise AttributeError("Scope metadata has not been set for this object!")
    return func.__requires_spotify_scopes__  # type: ignore


class OAuth2:
    """Helper object for Spotify OAuth2 operations.

    At a very basic level you can you oauth2 only for authentication.

    >>> oauth2 = OAuth2(client, 'some://redirect/uri')
    >>> print(oauth2.url)

    Working with scopes:

    >>> oauth2 = OAuth2(client, 'some://redirect/uri', scopes=['user-read-currently-playing'])
    >>> oauth2.set_scopes(user_read_playback_state=True)

    Parameters
    ----------
    client_id : :class:`str`
        The client id provided by spotify for the app.
    redirect_uri : :class:`str`
        The URI Spotify should redirect to.
    scopes : Optional[Iterable[:class:`str`], Dict[:class:`str`, :class:`bool`]]
        The scopes to be requested.
    state : Optional[:class:`str`]
        The state used to secure sessions.

    Attributes
    ----------
    attrs : Dict[:class:`str`, :class:`str`]
        The attributes used when constructing url parameters
    parameters : :class:`str`
        The URL parameters used
    url : :class:`str`
        The URL for OAuth2
    """

    _BASE = "https://accounts.spotify.com/authorize/?response_type=code&{parameters}"

    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        *,
        scopes: Optional[Union[Iterable[str], Dict[str, bool]]] = None,
        state: str = None,
    ):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.state = state
        self.__scopes: Set[str] = set()

        if scopes is not None:
            if not isinstance(scopes, dict) and hasattr(scopes, "__iter__"):
                scopes = {scope: True for scope in scopes}

            if isinstance(scopes, dict):
                self.set_scopes(**scopes)
            else:
                raise TypeError(
                    f"scopes must be an iterable of strings or a dict of string to bools"
                )

    def __repr__(self):
        return f"<spotfy.OAuth2: client_id={self.client_id!r}, scope={self.scopes!r}>"

    def __str__(self):
        return self.url

    # Alternate constructors

    @classmethod
    def from_client(cls, client, *args, **kwargs):
        """Construct a OAuth2 object from a `spotify.Client`."""
        return cls(client.http.client_id, *args, **kwargs)

    @staticmethod
    def url_only(**kwargs) -> str:
        """Construct a OAuth2 URL instead of an OAuth2 object."""
        oauth = OAuth2(**kwargs)
        return oauth.url

    # Properties

    @property
    def scopes(self):
        """:class:`frozenset` - A frozenset of the current scopes"""
        return frozenset(self.__scopes)

    @property
    def attributes(self):
        """Attributes used when constructing url parameters."""
        data = {"client_id": self.client_id, "redirect_uri": quote(self.redirect_uri)}

        if self.scopes:
            data["scope"] = quote(" ".join(self.scopes))

        if self.state is not None:
            data["state"] = self.state

        return data

    attrs = attributes

    @property
    def parameters(self) -> str:
        """:class:`str` - The formatted url parameters that are used."""
        return "&".join("{0}={1}".format(*item) for item in self.attributes.items())

    @property
    def url(self) -> str:
        """:class:`str` - The formatted oauth url used for authorization."""
        return self._BASE.format(parameters=self.parameters)

    # Public api

    def set_scopes(self, **scopes: Dict[str, bool]) -> None:
        r"""Modify the scopes for the current oauth2 object.

        Add or remove certain scopes from this oauth2 instance.

        >>> oauth2.set_scopes(user_read_playback_state=True, user-modify-playback-state=False)

        Parameters
        ----------
        \*\*scopes: Dict[:class:`str`, :class:`bool`]
            The scopes to enable or disable.
        """
        for scope_name, state in scopes.items():
            if state:
                self.__scopes.add(scope_name)
            else:
                self.__scopes.remove(scope_name)
