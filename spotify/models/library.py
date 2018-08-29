from spotify import _types

Track = _types.track
Album = _types.album


class Library:
    def __init__(self, client, user):
        self.user = user
        self.__client = client

    def __repr__(self):
        return '<spotify.Library: %s>' % (repr(self.user))

    def __eq__(self, other):
        return type(self) is type(other) and self.user == other.user

    def __ne__(self, other):
        return not self.__eq__(other)

    async def contains_albums(self, *albums):
        '''Check if one or more albums is already saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

        - albums (:class:`Artist`/:class:`str`)
            A sequence of artist objects or spotify IDs
        '''
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        return await self.user.http.is_saved_album(_albums)

    async def contains_tracks(self, *tracks):
        '''Check if one or more tracks is already saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

        - tracks (:class:`Track`/:class:`str`)
            A sequence of track objects or spotify IDs
        '''
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        return await self.user.http.is_saved_track(_tracks)

    async def get_tracks(self, *, limit=20, offset=0):
        '''Get a list of the songs saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

         - *limit* (Optional :class:`int`)
             The maximum number of objects to return. Default: 20. Minimum: 1. Maximum: 50.

         - *offset* (Optional :class:`int`)
             The index of the first object to return. Default: 0 (i.e., the first object)
        '''
        data = await self.user.http.saved_tracks(limit=limit, offset=offset)

        return [Track(self.__client, item['track']) for item in data['items']]

    async def get_albums(self, *, limit=20, offset=0):
        '''Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

         - *limit* (Optional :class:`int`)
             The limit on how many albums to retrieve for this artist (default is 20).

         - *offset* (Optional :class:`int`)
             The offset from where the api should start from in the albums.
        '''
        data = await self.user.http.saved_albums(limit=limit, offset=offset)

        return [Album(self.__client, item['album']) for item in data['items']]

    async def remove_albums(self, *albums):
        '''Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        **parameters**

        - albums (:class:`Artist`/:class:`str`)
            A sequence of artist objects or spotify IDs
        '''
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        await self.user.http.delete_saved_albums(','.join(_albums))

    async def remove_tracks(self, *tracks):
        '''Remove one or more tracks from the current user’s ‘Your Music’ library.

        **parameters**

        - tracks (:class:`Track`/:class:`str`)
            A sequence of track objects or spotify IDs
        '''
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        await self.user.http.delete_saved_tracks(','.join(_tracks))

    async def save_albums(self, *albums):
        '''Save one or more albums to the current user’s ‘Your Music’ library.

        **parameters**

        - albums (:class:`Artist`/:class:`str`)
            A sequence of artist objects or spotify IDs
        '''
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        await self.user.http.save_albums(','.join(_albums))

    async def save_tracks(self, *tracks):
        '''Save one or more tracks to the current user’s ‘Your Music’ library.

        **parameters**

        - tracks (:class:`Track`/:class:`str`)
            A sequence of track objects or spotify IDs
        '''
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        await self.user.http.save_tracks(','.join(_tracks))
