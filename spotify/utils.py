import functools
from urllib.parse import quote_plus as quote

def uri_to_id(string):
    if string[:8] == 'spotify:':
        return string.rsplit(':', maxsplit=1)[-1]
    return string

def ensure_http(func):
    @functools.wraps(func)
    async def decorator(self, *args, **kwargs):
        if not hasattr(self, 'http'):
            raise AttributeError('"{0}" has no attribute \'http\': To perform API requests {0} needs a HTTP presence.'.format(self))

        return await func(self, *args, **kwargs)

    return decorator



class OAuth2:
    _BASE = '{protocol}://accounts.spotify.com/authorize/?response_type=code&{parameters}'
    protocol = 'https'

    def __init__(self, client_id, redirect_uri, *, scope=None, state=None, secure=True):
        self.client_id = client_id
        self.redirect_uri = redirect_uri

        self.state = state
        self.scope = scope

        if not secure:
            self.protocol = 'http'

    def __repr__(self):
        return '<spotfy.OAuth2: client_id={0!r}, scope={1!r}>'.format(self.client_id, self.scope)

    def __str__(self):
        return self.url

    @staticmethod
    def url_(client_id, redirect_uri, *, scope=None, state=None, secure=True):
        attrs = {
            'client_id': client_id,
            'redirect_uri': quote(redirect_uri)
        }

        if scope is not None:
            attrs['scope'] = scope

        if state is not None:
            attrs['state'] = state

        parameters = '&'.join('{0}={1}'.format(*item) for item in attrs.items())
        protocol = 'https' if secure else 'http'

        return OAuth2._BASE.format(protocol=protocol, parameters=parameters)

    @property
    def attrs(self):
        data =  {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
        }

        if self.scope is not None:
            data['scope'] = self.scope

        if self.state is not None:
            data['state'] = self.state

        return data

    @property
    def parameters(self):
        return '&'.join('{0}={1}'.format(*item) for item in self.attrs.items())

    @property
    def url(self):
        return self._BASE.format(protocol=self.protocol, parameters=self.parameters)


class _spotify__lookup(dict):
    __types = ['artist', 'track', 'user', 'playlist', 'album', 'library', 'playlist_track']

    def __getattribute__(self, key):
        _types = object.__getattribute__(self, '_spotify__lookup__types')

        if key in _types:
            def _lookup(*args, **kwargs):
                return self[key](*args, **kwargs)

            return _lookup

        return object.__getattribute__(self, key)
