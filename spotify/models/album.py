from .common import Image

from spotify import _types

Artist = _types.artist
Track = _types.track

class Album:
    def __init__(self, client, data):
        self.__client = client
        self.__data = data

        self.artists = [Artist(client, artist) for artist in data.get('artists', [])]

    def __repr__(self):
        return '<spotify.Album: "%s">' %(self.name or self.id or self.uri)

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri

    def __neq__(self, other):
        return not self == other

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
    def album_group(self):
        return self.__data.get('album_group')

    @property
    def album_type(self):
        return self.__data.get('album_type')

    @property
    def release_date(self):
        return self.__data.get('release_date')

    @property
    def release_date_precision(self):
        return self.__data.get('release_date_precision')

    @property
    def genre(self):
        return self.__data.get('genres')

    @property
    def label(self):
        return self.__data.get('label')

    @property
    def popularity(self):
        return self.__data.get('popularity')

    @property
    def copyrights(self):
        return self.__data.get('copyrights')    

    @property
    def markets(self):
        return self.__data.get('avaliable_markets')

    @property
    def images(self):
        return [Image(**image) for image in self.__data.get('images')]    

    async def total_tracks(self):
        return (await self.__client.http.album_tracks(self.id, limit=1, offset=0)).get('total')

    async def get_tracks(self, *, limit=20, offset=0):
        '''get the albums tracks from spotify.
        
        **parameters**

         - *limit* (Optional :class:`int`)
             The limit on how many tracks to retrieve for this album (default is 20).

         - *offset* (Optional :class:`int`)
             The offset from where the api should start from in the tracks.
        '''
        data = await self.__client.http.album_tracks(self.id, limit=limit, offset=offset)
        return [Track(self.__client, item) for item in data['items']]

    async def get_all_tracks(self, *, market='us'):
        '''loads all of the albums tracks, depending on how many the album has this may be a long operation.

        **parameters**

        - *market* (Optional :class:`str`)
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.
        '''
        tracks = []
        offset = 0
        total = (await self.__client.http.album_tracks(self.id, limit=1, offset=0, market='us'))['total']

        while len(tracks) < total:
            data = await self.__client.http.album_tracks(self.id, limit=50, offset=offset, market='us')
            offset += 50

            tracks += [Track(self.__client, item) for item in data['items']]

        return tracks
