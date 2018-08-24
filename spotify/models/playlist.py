from spotify import _types
from .common import Image

User = _types.user
Track = _types.track
PlaylistTrack = _types.playlist_track


class PartialTracks:
    __slots__ = ('data', '__client', '__iter')

    def __init__(self, data, client):
        self.data = data
        self.__client = client
        self.__iter = None

    def __repr__(self):
        return '<spotify.PartialTracks: total="%s">' % self.data['total']

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.__iter is None:
            async def _iter_build():
                data = await self.__client.http.request(('GET', self.data['href']))

                for track in data['items']:
                    yield PlaylistTrack(self.__client, track)

            self.__iter = _iter_build()

        return await self.__iter.__anext__()

    async def build(self):
        '''get the track object for each link in the partial tracks data'''
        data = await self.__client.http.request(('GET', self.data['href']))
        return [PlaylistTrack(self.__client, track) for track in data['items']]


class Playlist:
    def __init__(self, client, data):
        self.__client = client
        self.__data = data

        self.owner = User(client, data=data.get('owner'))
        self._tracks = PartialTracks(data.get('tracks'), client)

    def __repr__(self):
        return '<spotify.Playlist: "%s">' % (self.name)

    def __str__(self):
        return self.uri

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def id(self):
        return self.__data.get('id')

    @property
    def name(self):
        return self.__data.get('name')

    @property
    def href(self):
        return self.__data.get('href')

    @property
    def uri(self):
        return self.__data.get('uri')

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
        '''Get the tracks of a playlist'''

        if isinstance(self._tracks, PartialTracks):
            total = self._tracks.data['total']
            self._tracks = await self._tracks.build()

        offset = 0
        while len(self.tracks) < total:
            data = await self.__client.http.get_playlist_tracks(self.owner.id, self.id, limit=50, offset=offset)

            self._tracks += [PlaylistTrack(self.__client, item) for item in data['items']]
            offset += 50

        return list(self._tracks)
