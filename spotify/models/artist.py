from spotify import _types

Track = _types.track

class Artist:
    def __init__(self, client, data):
        self.__client = client
        self.__data = data

    def __repr__(self):
        return '<spotify.Artist: "%s">' %(self.name)

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
