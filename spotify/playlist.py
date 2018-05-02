##
# -*- coding: utf-8 -*-
##
from .model import SpotifyModel, Image
from .utils import _unique_cache
from .http import Route


class PartialTracks:
    __slots__ = ['data']

    def __init__(self, data):
        self.data = data

    async def build(self, client):
        '''get the track object for each link in the partial tracks data'''
        link = self.data['href']
        route = Route('GET', '')
        route.url = link

        raw = []
        data = await client.http.request(route)

        for track in data['items']:
            model = client._build('_tracks', track['track'])
            raw.append(model)

        return raw

class Playlist(SpotifyModel):
    __slots__ = ['_client', '_cache', 'id', 'href', 'name', 'snapshot_id', 'uri', 'public', 'collaborative', 'owner', 'images', 'external_urls', 'total']

    def __init__(self, client, data):
        self._client = client
        self._cache = []
        self.is_simple = ('followers' not in data)

        self.id = data.get('id')
        self.href = data.get('href')
        self.name = data.get('name')
        self.snapshot_id = data.get('snapshot_id')
        self.uri = data.get('uri')

        self.public = data.get('public')
        self.collaborative = data.get('collaborative')

        self.owner = data.get('owner') # client._build(data.get('owner'), 'user')

        self.images = [Image(**image) for image in data.get('images')]
        self.external_urls = data.get('external_urls') # EXTERNAL URL OBJECT

        if not self.is_simple:
            self._cache += [client._build('_tracks', track) for track in data.get('tracks')]
            self.total = len(self._cache)
        else:
            self._cache += [PartialTracks(data.get('tracks'))]
            self.total = int(self._cache[-1].data['total'])

        client._cache.add('_playlists', self)

    def __repr__(self):
        return '<spotify.Playlist: "%s">' %(self.name)

    @property
    def tracks(self):
        '''retrive the playlists tracks from the internal cache'''
        return [obj for obj in self._cache]

    async def get_tracks(self):
        '''Get the tracks of a playlist'''

        for item in self._cache:
            if isinstance(item, PartialTracks):
                for track in (await item.build(self._client)):
                    _unique_cache(self._cache, track)

        if len(self._cache) != self.total:
            data = await self._client.http.playlist_tracks(self.owner.id, self.id)
            for track in data['items']:
                model = self._client._build('_tracks', track)
                _unique_cache(self._cache, model)

        return [track for track in self._cache]
