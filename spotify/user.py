##
# -*- coding: utf-8 -*-
##
from .http import HTTPUserClient
from .playlist import Playlist
from .model import SpotifyModel, Image

from .utils import ensure_http, _unique_cache

class User(SpotifyModel):
    __slots__ = ['http', '_client', '_cache', 'display_name', 'external_urls', 'followers', 'id', 'href', 'uri', 'images', 'birthdate', 'country', 'email', 'premium', 'private', 'scopes']

    def __init__(self, client, **kwargs):
        self._client = client
        self._cache = []

        if kwargs.get('token'):
            self.http = HTTPUserClient(kwargs.get('token'))

        if kwargs.get('data'):
            self._parse(kwargs.get('data'), kwargs.get('private', False))

    def _parse(self, data, private=False):
        self.private = private

        self.display_name = data.get('display_name')
        self.external_urls = data.get('external_urls')
        self.followers = data.get('followers').get('total')

        self.id = data.get('id')
        self.href = data.get('href')
        self.uri = data.get('uri')

        self.images = [Image(**image) for image in data.get('images')]

        if private:
            self.birthdate = data.get('birthdate')
            self.country = data.get('country')
            self.email = data.get('email')
            self.premium = (data.get('product') == 'premium')

    def __repr__(self):
        try:
            return '<spotify.User: "%s">' %(self.display_name or self.id)
        except AttributeError:
            return '<spotify.User: BLANK_USER>'

    async def add_tracks(self, playlist, *tracks):
        ensure_http(self)

        playlist_id = (playlist.id if isinstance(playlist, Playlist) else playlist)
        tracks = [(track.uri if not isinstance(track, str) else track) for track in tracks]
        return await self.http.add_playlist_tracks(self.id, playlist_id, tracks=','.join(tracks))

    async def replace_tracks(self, playlist, *tracks):
        ensure_http(self)

        playlist_id = (playlist.id if isinstance(playlist, Playlist) else playlist)
        tracks = [(track.uri if not isinstance(track, str) else track) for track in tracks]
        return await self.http.replace_playlist_tracks(self.id, playlist_id, uris=','.join(tracks))

    async def remove_tracks(self, playlist, *tracks):
        ensure_http(self)

        playlist_id = (playlist.id if isinstance(playlist, Playlist) else playlist)
        tracks = [(track.uri if not isinstance(track, str) else track) for track in tracks]
        return await self.http.remove_playlist_tracks(self.id, playlist_id, [{'uri': track} for track in tracks])

    async def reorder_tracks(self, playlist, range_info, *, snapshot_id=None):
        ensure_http(self)

        start, length, insert = range_info
        playlist_id = (playlist.id if isinstance(playlist, Playlist) else playlist)
        return await self.http.reorder_playlists_tracks(self.id, playlist_id, start, length, insert, snapshot_id=snapshot_id)

    async def edit_playlist(self, playlist, **new):
        ensure_http(self)

        playlist_id = (playlist.id if isinstance(playlist, Playlist) else playlist)
        data = {key: value for key, value in new.items() if key in ('name', 'public', 'collaborative', 'description')}
        return await self.http.change_playlist_details(self.id, playlist_id, data=data)

    async def edit_playlist_cover(self, playlist, image):
        playlist_id = (playlist.id if isinstance(playlist, Playlist) else playlist)
        return await self.http.upload_playlist_cover_image(self.id, playlist_id, image)

    async def create_playlist(self, **data):
        ensure_http(self)

        data = {key: value for key, value in data.items() if key in ('name', 'public', 'collaborative', 'description')}
        return self._client._construct(await self.http.create_playlist(self.id, data=data), 'playlist')

    @property
    def playlists(self):
        return [playlist for playlist in self._cache if playlist in self._client._cache._playlists]

    async def get_playlists(self, *, limit=20, offset=1):
        ensure_http(self)

        raw = []
        data = await self.http.get_playlists(self.id, limit=limit, offset=offset)

        for playlist in data['items']:
            model = await self._client._construct(playlist, 'playlist')
            _unique_cache(self._cache, model)
            raw.append(model)

        return raw
