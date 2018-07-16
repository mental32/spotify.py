from spotify import _types
from .common import Image

User = _types.user
Track = _types.track

class PartialTracks:
    __slots__ = ['data']

    def __init__(self, data):
        self.data = data

    async def build(self, client):
        '''get the track object for each link in the partial tracks data'''
        link = self.data['href']
        data = await client.http.request(('GET', link))
        return [Track(client, track['track']) for track in data['items']]

class Playlist:
    def __init__(self, client, data):
        self.__client = client
        self.__data = data

        self.owner = User(client, data=data.get('owner'))
        self._tracks = PartialTracks(data.get('tracks'))

    def __repr__(self):
        return '<spotify.Playlist: "%s">' %(self.name)

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
    def images(self):
        return [Image(**image) for image in self.__data.get('images')]

    @property
    def tracks(self):
        return self._tracks

    async def get_tracks(self):
        '''Get the tracks of a playlist'''

        if isinstance(self._tracks, PartialTracks):
            total = self._tracks.data['total']
            self._tracks = await self._tracks.build(self.__client)

        if len(self.tracks) != total:
            data = await self.__client.http.get_playlist_tracks(self.owner.id, self.id)

            for item in data['items']:
                self._tracks.append(Track(self.__client, item))

        return [track for track in self._tracks]
