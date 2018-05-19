##
# -*- coding: utf-8 -*-
##
from .utils import _filter_options

class Library:
    '''method wrapper for a users library'''

    def __init__(self, user):
        self.user = user
        self._cache = set()

    @property
    def _client(self):
        return self.user._client

    async def contains_albums(self, *albums):
        '''Check if one or more albums is already saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

        - albums (:class:`Artist`/:class:`str`)
            A sequence of artist objects or spotify IDs
        '''
        albums = [(album.id if self._client._istype(album, 'album') else album) for album in albums]
        return await self.user.http.is_saved_album(albums)

    async def contains_tracks(self, *tracks):
        '''Check if one or more tracks is already saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

        - tracks (:class:`Track`/:class:`str`)
            A sequence of track objects or spotify IDs
        '''
        tracks = [(track.id if self._client._istype(track, 'track') else track) for track in tracks]
        return await self.user.http.is_saved_track(tracks)

    async def get_tracks(self, *, limit=20, offset=0):
        '''Get a list of the songs saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

         - *limit* (Optional :class:`int`)
             The maximum number of objects to return. Default: 20. Minimum: 1. Maximum: 50.

         - *offset* (Optional :class:`int`)
             The index of the first object to return. Default: 0 (i.e., the first object)
        '''
        raw = []
        opts = _filter_options(limit=limit, offset=offset)
        data = await self.user.http.saved_tracks(**opts)

        for track in data['items']:
            model = self._client._build('_tracks', track)
            self._cache.add(model.id)
            raw.append(model)

        return raw

    async def get_albums(self, *, limit=20, offset=0):
        '''Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

         - *limit* (Optional :class:`int`)
             The limit on how many albums to retrieve for this artist (default is 20).

         - *offset* (Optional :class:`int`)
             The offset from where the api should start from in the albums.
        '''
        raw = []
        data = await self.user.http.saved_albums(limit=limit, offset=offset)

        for album in data['items']:
            model = self._client._build(album, _type='album')
            self._cache.add(model.id)
            raw.append(model)

        return raw

    async def remove_albums(self, *albums):
        '''Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

        - albums (:class:`Artist`/:class:`str`)
            A sequence of artist objects or spotify IDs
        '''
        albums = [(album.id if self._client._istype(album, 'album') else album) for album in albums]
        await self.user.http.delete_saved_albums(','.join(albums))

    async def remove_tracks(self, *tracks):
        '''Remove one or more tracks from the current user’s ‘Your Music’ library.

        **parameters**

        - tracks (:class:`Track`/:class:`str`)
            A sequence of track objects or spotify IDs
        '''
        tracks = [(track.id if self._client._istype(track, 'track') else track) for track in tracks]
        await self.user.http.delete_saved_tracks(','.join(tracks))

    async def save_albums(self, *albums):
        '''Save one or more albums to the current user’s ‘Your Music’ library.

        **parameters**

        - albums (:class:`Artist`/:class:`str`)
            A sequence of artist objects or spotify IDs
        '''
        albums = [(album.id if self._client._istype(album, 'album') else album) for album in albums]
        await self.user.http.save_albums(','.join(albums))

    async def save_tracks(self, *tracks):
        '''Save one or more tracks to the current user’s ‘Your Music’ library.

        **parameters**

        - tracks (:class:`Track`/:class:`str`)
            A sequence of track objects or spotify IDs
        '''
        tracks = [(track.id if self._client._istype(track, 'track') else track) for track in tracks]
        await self.user.http.save_tracks(','.join(tracks))
