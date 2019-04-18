from functools import partial

from . import SpotifyBase, URIBase, Track, PlaylistTrack, Image


class PartialTracks(SpotifyBase):
    """  # TODO: Add PartialTracks documentation.
    """
    __slots__ = ('total', '__func', '__iter', '__client')

    def __init__(self, client, data):
        self.total = data['total']
        self.__client = client
        self.__func = partial(client.http.request, ('GET', data['href']))
        self.__iter = None

    def __repr__(self):
        return '<spotify.PartialTracks: total="%s">' % self.total

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.__iter is None:
            self.__iter = iter((await self.__func())['items'])

        try:
            track = next(self.__iter)
        except StopIteration:
            raise StopAsyncIteration
        else:
            return PlaylistTrack(self.__client, track)

    async def build(self):
        """get the track object for each link in the partial tracks data"""
        data = await self.__func()
        return list(PlaylistTrack(self.__client, track) for track in data['items'])


class Playlist(URIBase):  # TODO: __data is removed but not done on Playlist.
    """A Spotify Playlist.

    Attributes
    ----------

    """
    __slots__ = ('__client', '_type', 'owner', 'total_tracks', 'id', 'name', 'href', 'uri')

    def __init__(self, client, data):
        self.__client = client

        self.owner = User(client, data=data.get('owner'))
        self._tracks = PartialTracks(client, data.get('tracks'))
        self.total_tracks = self._tracks.data['total']

        self.id = data.pop('id')
        self.name = data.pop('name')
        self.href = data.pop('href')
        self.uri = data.pop('uri')

        self.__data = data

    def __repr__(self):
        return '<spotify.Playlist: "%s">' % self.name

    @property
    def public(self):
        return self.__data.get('public')

    @property
    def collaborative(self):
        return self.__data.get('collaborative')

    @property
    def description(self):
        return self.__data.get('description')

    @property
    def images(self):
        return [Image(**image) for image in self.__data.get('images')]

    @property
    def tracks(self):
        return self._tracks

    async def get_tracks(self):
        """Get all playlist tracks from the playlist.
        """
        if isinstance(self._tracks, PartialTracks):
            return await self._tracks.build()

        offset = 0
        while len(self.tracks) < self.total_tracks:
            data = await self.__client.http.get_playlist_tracks(self.owner.id, self.id, limit=50, offset=offset)

            _tracks += [PlaylistTrack(self.__client, item) for item in data['items']]
            offset += 50

        self.total_tracks = len(self._tracks)
        return list(self._tracks)
