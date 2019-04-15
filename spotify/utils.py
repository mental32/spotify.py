import functools
from contextlib import contextmanager
from urllib.parse import quote_plus as quote

from .errors import SpotifyException



@contextmanager
def clean(l: dict, *names):
    yield
    for name in names:
        l.pop(name)


def ensure_http(func):
    @functools.wraps(func)
    async def decorator(self, *args, **kwargs):
        if not hasattr(self, 'http'):
            raise SpotifyException('{0!r} has no HTTP presence to perform API requests'.format(self))

        return await func(self, *args, **kwargs)

    return decorator


class OAuth2:
    """Helper object for Spotify OAuth2 operations.

    Parameters
    ----------
    client_id : str
        The client id provided by spotify for the app.
    redirect_uri : str
        The URI Spotify should redirect to.
    scope : str
        The scopes to be requested.
    state : str
        The state used to secure sessions.

    Attributes
    ----------
    attrs : Dict[str, str]
        The attributes used when constructing url parameters
    parameters : str
        The URL parameters used
    url : str
        The URL for OAuth2
    """

    _BASE = 'https://accounts.spotify.com/authorize/?response_type=code&{parameters}'

    def __init__(self, client_id, redirect_uri, *, scope=None, state=None, secure=True):
        self.client_id = client_id
        self.redirect_uri = redirect_uri

        self.state = state
        self.scope = scope

    def __repr__(self):
        return '<spotfy.OAuth2: client_id={0!r}, scope={1!r}>'.format(self.client_id, self.scope)

    def __str__(self):
        return self.url

    @classmethod
    def from_client(cls, client, *args, **kwargs):
        """Construct a OAuth2 object from a  `spotify.Client`."""
        return cls(client.http.client_id, *args, **kwargs)

    @staticmethod
    def url_(client_id: str, redirect_uri: str, *, scope: str = None, state: str = None, secure: bool = True) -> str:
        """Construct a OAuth2 URL instead of an OAuth2 object."""
        attrs = {
            'client_id': client_id,
            'redirect_uri': quote(redirect_uri)
        }

        if scope is not None:
            attrs['scope'] = quote(scope)

        if state is not None:
            attrs['state'] = state

        parameters = '&'.join('{0}={1}'.format(*item) for item in attrs.items())

        return OAuth2._BASE.format(parameters=parameters)

    @staticmethod
    def url_only(*args, **kwargs):
        """Construct a OAuth2 URL instead of an OAuth2 object."""
        return OAuth2.url_(*args, **kwargs)

    @property
    def attrs(self):
        """Attributes used when constructing url parameters."""
        data = {
            'client_id': self.client_id,
            'redirect_uri': quote(self.redirect_uri),
        }

        if self.scope is not None:
            data['scope'] = quote(self.scope)

        if self.state is not None:
            data['state'] = self.state

        return data

    @property
    def parameters(self) -> str:
        """URL parameters used."""
        return '&'.join('{0}={1}'.format(*item) for item in self.attrs.items())

    @property
    def url(self) -> str:
        """Return a URL for an OAuth2."""
        return self._BASE.format(parameters=self.parameters)
