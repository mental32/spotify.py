##
# -*- coding: utf-8 -*-
##
from .model import SpotifyModel


class Track(SpotifyModel):
    __slots__ = ['_client', 'available_markets', 'href', 'id', 'name', 'uri', 'disc_number', 'duration', 'explicit', 'is_playable', 'artists', 'external_urls', 'external_ids', 'album']

    def __init__(self, client, data):
        self._client = client
        self.is_simple = ('album' not in data)
 
        self.available_markets = data.get('available_markets')
        self.href = data.get('href')
        self.id = data.get('id')
        self.name = data.get('name')
        self.uri = data.get('uri')

        self.disc_number = data.get('disc_number')
        self.duration = data.get('duration_ms')

        self.explicit = data.get('explicit')
        self.is_playable = data.get('is_playable')

        self.artists = [client._build('_artists', _data) for _data in data.get('artists')]
        self.external_urls = data.get('external_urls') # EXTERNAL URL OBJECT

        if not self.is_simple:
            self.album = client._build('_albums', data.get('album'))
            self.external_ids = data.get('external_ids')   # EXTERNAL ID OBJECT

        client._cache.add('_tracks', self)

    def __repr__(self):
        return '<spotify.Track: "%s">' %(self.name)

    async def audio_analysis(self):
        '''Get a detailed audio analysis for the track'''
        return await self._client.http.track_audio_analysis(self.id)

    async def audio_features(self):
        '''Get audio feature information for the track'''
        return await self._client.http.track_audio_features(self.id)
