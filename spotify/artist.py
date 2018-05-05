##
# -*- coding: utf-8 -*-
##
from .model import SpotifyModel, Image
from .utils import _filter_options

class Artist(SpotifyModel):
    __slots__ = ['_client', '_cache', 'id', 'href', 'name', 'uri', 'external_urls', 'followers', 'genres', 'images', 'popularity']

    def __init__(self, client, data):
        self._cache = {}
        self._client = client
        self.is_simple = ('followers' not in data)

        self.id = data.get('id')
        self.href = data.get('href')
        self.name = data.get('name')
        self.uri = data.get('uri')

        self.external_urls = data.get('external_urls')

        if not self.is_simple:
            self.genres = data.get('genres')

            self.followers = data.get('followers').get('total')
            self.popularity = data.get('popularity')

            self.images = [Image(**image) for image in data.get('images')]

        client._cache.add('_artists', self)

    def __repr__(self):
        return '<spotify.Artist: "%s">' %(self.name)

    @property
    def _shallow_cache(self):
        return [obj for obj in self._cache.values()] 

    @property
    def albums(self):
        '''retrive the artists albums from the internal cache'''
        return [item for item in self._shallow_cache if item in self._client.albums]

    async def get_albums(self, *, limit=20, offset=0, include_groups=None, market=None):
        '''get the artists albums from spotify.
        
        **parameters**

         - *limit* (Optional :class:`int`)
             The limit on how many albums to retrieve for this artist (default is 20).

         - *offset* (Optional :class:`int`)
             The offset from where the api should start from in the albums.
        '''
        args = _filter_options(include_groups=None, market=None)
        data = await self._client.http.artist_albums(self.id, limit=limit, offset=offset, **args)

        for album in data['items']:
            model = self._client._construct(album, _type='album')
            self._cache[model.id] = model

        return self._shallow_cache

    async def load_all_albums(self, *, include_groups=None, market='US'):
        '''loads all of the artists albums, depending on how many the artist has this may be a long operation.

        **parameters**

        - *market* (Optional :class:`str`)
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.
        '''
        offset = 0
        args = _filter_options(include_groups=None, market=None)

        total = (await self._client.http.artist_albums(self.id, limit=1, offset=0, **args))['total']

        while len(self.albums) != total:
            data = await self._client.http.artist_albums(self.id, limit=50, offset=offset, **args)
            offset += 50

            for album in data['items']:
                model = self._client._construct(album, _type='album')
                self._cache[model.id] = model

        return self._shallow_cache

    @property
    def tracks(self):
        '''retrive the artists tracks from the internal cache'''
        return [item for item in self._shallow_cache if item in self._client.tracks]

    async def top_tracks(self, country='US'):
        '''Get Spotify catalog information about an artist’s top tracks by country.
        
        **parameters**

        - *country* (:class:`str`)
            The country to search for, it defaults to 'US'.
        '''

        tracks = []
        for track in (await self._client.http.artist_top_tracks(self.id, country=country))['tracks']:
            model = self._client._build('_tracks', track)
            self._cache[model.id] = model
            tracks.append(model)

        return tracks

    async def related_artists(self):
        '''Get Spotify catalog information about artists similar to a given artist. Similarity is based on analysis of the Spotify community’s listening history.'''

        artists = []
        for artist in (await self._client.http.artist_related_artists(self.id))['artists']:
            model = self._client._build('_artists', artist)
            self._cache[model.id] = model
            artists.append(model)

        return artists
