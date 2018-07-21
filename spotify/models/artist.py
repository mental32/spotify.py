from spotify import _types

Track = _types.track
Album = _types.album

class Artist:
    def __init__(self, client, data):
        self.__client = client
        self.__data = data

    def __repr__(self):
        return '<spotify.Artist: "%s">' %(self.name)

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

    async def get_albums(self, *, limit=20, offset=0, include_groups=None, market=None):
        '''get the artists albums from spotify.
        
        **parameters**

         - *limit* (Optional :class:`int`)
             The limit on how many albums to retrieve for this artist (default is 20).

         - *offset* (Optional :class:`int`)
             The offset from where the api should start from in the albums.
        '''
        data = await self.__client.http.artist_albums(self.id, limit=limit, offset=offset, include_groups=include_groups, market=market)
        return [Album(self.__client, item) for item in data['items']]

    async def get_all_albums(self, *, market='US'):
        '''loads all of the artists albums, depending on how many the artist has this may be a long operation.

        **parameters**

        - *market* (Optional :class:`str`)
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.
        '''
        albums = []
        offset = 0
        total = await self.total_albums(market=market)

        while len(albums) < total:
            data = await self.__client.http.artist_albums(self.id, limit=50, offset=offset, market=market)

            offset += 50
            albums += [Album(self.__client, item) for item in data['items']]

        return albums

    async def total_albums(self, *, market=None):
        '''get the total amout of tracks in the album.'''
        kwargs = {'limit': 1, 'offset': 0}

        if market:
            kwargs['market'] = market

        return (await self.__client.http.artist_albums(self.id, **kwargs)).get('total')

    async def top_tracks(self, country='US'):
        '''Get Spotify catalog information about an artist’s top tracks by country.
        
        **parameters**

        - *country* (:class:`str`)
            The country to search for, it defaults to 'US'.
        '''
        data = (await self.__client.http.artist_top_tracks(self.id, country=country))['tracks']

        return [Track(self.__client, item) for item in data]

    async def related_artists(self):
        '''Get Spotify catalog information about artists similar to a given artist. Similarity is based on analysis of the Spotify community’s listening history.'''
        data = (await self.__client.http.artist_related_artists(self.id))['artists']

        return [Artist(self.__client, item) for item in data]
