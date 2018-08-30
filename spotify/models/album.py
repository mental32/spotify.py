from .common import Image

from spotify import _types

Artist = _types.artist
Track = _types.track


class Album:
    __slots__ = ('__client', '_type', 'id', 'name', 'href', 'uri', '__data', 'artists')

    def __init__(self, client, data):
        self.__client = client
        self._type = _types[data['type']]

        self.id = data.pop('id')
        self.name = data.pop('name')
        self.href = data.pop('href')
        self.uri = data.pop('uri')

        self.__data = data
        self.artists = [Artist(client, artist) for artist in data.get('artists', [])]

    def __repr__(self):
        return '<spotify.Album: "%s">' % (self.name or self.id or self.uri)

    def __str__(self):
        return self.uri

    def __eq__(self, other):
        return type(self) is type(other) and self.uri == other.uri

    def __ne__(self, other):
        return not self.__eq__(other)

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

    async def total_tracks(self, *, market=None):
        '''get the total amout of tracks in the album.'''
        kwargs = {'limit': 1, 'offset': 0}

        if market:
            kwargs['market'] = market

        return (await self.__client.http.album_tracks(self.id, **kwargs)).get('total')

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

    async def get_all_tracks(self, *, market='US'):
        '''loads all of the albums tracks, depending on how many the album has this may be a long operation.

        **parameters**

        - *market* (Optional :class:`str`)
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.
        '''
        tracks = []
        offset = 0
        total = await self.total_tracks(market=market)

        while len(tracks) < total:
            data = await self.__client.http.album_tracks(self.id, limit=50, offset=offset, market=market)

            offset += 50
            tracks += [Track(self.__client, item) for item in data['items']]

        return tracks
