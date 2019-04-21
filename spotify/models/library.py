from typing import Sequence, Union, List

from . import SpotifyBase
from .track import Track
from .album import Album


class Library(SpotifyBase):
    """A Spotify Users Library.

    Attributes
    ----------
    user : Spotify.User
        The user which this library object belongs to.
    """
    def __init__(self, client, user):
        self.user = user
        self.__client = client

    def __repr__(self):
        return '<spotify.Library: %s>' % (repr(self.user))

    def __eq__(self, other):
        return type(self) is type(other) and self.user == other.user

    def __ne__(self, other):
        return not self.__eq__(other)

    async def contains_albums(self, *albums: Sequence[Union[str, Album]]) -> List[bool]:
        """Check if one or more albums is already saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        albums : Union[Album, str]
            A sequence of artist objects or spotify IDs
        """
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        return await self.user.http.is_saved_album(_albums)

    async def contains_tracks(self, *tracks: Sequence[Union[str, Track]]) -> List[bool]:
        """Check if one or more tracks is already saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        tracks : Union[Track, str]
            A sequence of track objects or spotify IDs
        """
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        return await self.user.http.is_saved_track(_tracks)

    async def get_tracks(self, *, limit=20, offset=0) -> List[Track]:
        """Get a list of the songs saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first item to return. Default: 0
        """
        data = await self.user.http.saved_tracks(limit=limit, offset=offset)

        return [Track(self.__client, item['track']) for item in data['items']]

    async def get_albums(self, *, limit=20, offset=0) -> List[Album]:
        """Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first item to return. Default: 0
        """
        data = await self.user.http.saved_albums(limit=limit, offset=offset)

        return [Album(self.__client, item['album']) for item in data['items']]

    async def remove_albums(self, *albums):
        """Remove one or more albums from the current user’s ‘Your Music’ library.

        Parameters
        ----------
        albums : Sequence[Union[Album, str]]
            A sequence of artist objects or spotify IDs
        """
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        await self.user.http.delete_saved_albums(','.join(_albums))

    async def remove_tracks(self, *tracks):
        """Remove one or more tracks from the current user’s ‘Your Music’ library.

        Parameters
        ----------
        tracks : Sequence[Union[Track, str]]
            A sequence of track objects or spotify IDs
        """
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        await self.user.http.delete_saved_tracks(','.join(_tracks))

    async def save_albums(self, *albums):
        """Save one or more albums to the current user’s ‘Your Music’ library.

        Parameters
        ----------
        albums : Sequence[Union[Album, str]]
            A sequence of artist objects or spotify IDs
        """
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        await self.user.http.save_albums(','.join(_albums))

    async def save_tracks(self, *tracks):
        """Save one or more tracks to the current user’s ‘Your Music’ library.

        Parameters
        ----------
        tracks : Sequence[Union[Track, str]]
            A sequence of track objects or spotify IDs
        """
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        await self.user.http.save_tracks(','.join(_tracks))
