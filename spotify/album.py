##
# -*- coding: utf-8 -*-
##
from .model import SpotifyModel, Image

_swap = {

}

class Album(SpotifyModel):
    __slots__ = ['_cache', '_client', 'type', 'group', 'href', 'id', 'label', 'name', 'release_date', 'release_date_precision', 'uri', 'popularity', 'avaliable_markets', 'genres', 'external_ids', 'artists', 'external_urls', 'copyrights', 'images']

    def __init__(self, client, data):
        # data is defined in order:
        # str, int, object, seq: str, int, objects
        self._cache = {}
        self._client = client
        self.is_simple = ('tracks' not in data)

        if self.is_simple:
            self.group = data.get('album_group')

        self.type = data.get('album_type')
        self.href = data.get('href')
        self.id = data.get('id')
        self.name = data.get('name')
        self.release_date = data.get('release_date')
        self.release_date_precision = data.get('release_date_precision')
        self.uri = data.get('uri')

        self.avaliable_markets = data.get('avaliable_markets')

        self.artists = [client._build('_artists', _data) for _data in data.get('artists')]
        self.images = [Image(**image) for image in data.get('images')]
        self.external_urls = data.get('external_urls') # EXTERNAL URL OBJECT

        if not self.is_simple:
            self.genres = data.get('genres')
            self.label = data.get('label')

            self.popularity = data.get('popularity')

            self.external_ids = data.get('external_ids')   # EXTERNAL ID OBJECT
            self.copyrights = data.get('copyrights')       # COPYRIGHT OBJECT

            for track in (client._build('_tracks', _data) for _data in data.get('tracks').get('items', [])):
                self._cache[track.id] = track

        client._cache.add('_albums', self)

    def __repr__(self):
        return '<spotify.Album: "%s">' %(self.name)

    @property
    def _shallow_cache(self):
        return [obj for obj in self._cache.values()]

    def _update(self, new):
        '''updates the current object with a new one'''
        for key, value in new.items():
            setattr(self, _swap.get(key, key), value)

    @property
    def tracks(self):
        '''return the track objects for this album found in cache'''
        return self._shallow_cache

    async def get_tracks(self):
        '''load the albums tracks from spotify'''
        raw = []
        data = await self._client.http.album_tracks(self.id)

        for track in data['items']:
            model = self._client._build('_tracks', track)
            self._cache[model.id] = model
            raw.append(model)

        return raw

    async def make_full(self):
        '''updates the Album object to a full album object if its a simplified one'''
        if self.is_simple:
            data = await self._client.http.album(self.id)

            if hasattr(self, 'group'):
                del self.group

            self.genres = data.get('genres')
            self.label = data.get('label')

            self.popularity = data.get('popularity')

            self.external_ids = data.get('external_ids')   # EXTERNAL ID OBJECT
            self.copyrights = data.get('copyrights')       # COPYRIGHT OBJECT

            for track in (self._client._build('_tracks', _data) for _data in data.get('tracks').get('items', [])):
                self._cache[track.id] = track
