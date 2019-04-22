import spotify

class SpotifyBase:
    """The base class all Spotify models should derive from."""
    __slots__ = ()

    def __new__(cls, client, *args, **kwargs):
        if not isinstance(client, spotify.Client):
            raise TypeError(f'{cls!r}: expected client argument to be an instance of spotify.Client. instead got {type(client)}')

        elif hasattr(client, '__client_thread__'):
            cls = getattr(spotify.sync.models, cls.__name__)

        return object.__new__(cls)

    async def from_href(self):
        """Get the full object from spotify with a `href` attribute."""
        if not hasattr(self, 'href'):
            raise TypeError('Spotify object has no `href` attribute, therefore cannot be retrived')

        elif hasattr(self, 'http'):
            return await self.http.request(('GET', self.href))

        else:
            cls = type(self)

        try:
            client = getattr(self, '_{0}__client'.format(cls.__name__))
        except AttributeError:
            raise TypeError('Spotify object has no way to access a HTTPClient.')
        else:
            http = client.http

        data = await http.request(('GET', self.href))

        return cls(client, data)


class URIBase(SpotifyBase):
    """Base class used for inheriting magic methods for models who have URIs."""

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.uri
