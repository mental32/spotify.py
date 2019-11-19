from typing import Sequence, Union, List

from ..oauth import set_required_scopes
from . import SpotifyBase
from .track import Track
from .album import Album


class Library(SpotifyBase):
    """A Spotify Users Library.

    Attributes
    ----------
    user : :class:`Spotify.User`
        The user which this library object belongs to.
    """

    def __init__(self, client, user):
        self.user = user
        self.__client = client

    def __repr__(self):
        return f"<spotify.Library: {self.user!r}>"

    def __eq__(self, other):
        return type(self) is type(other) and self.user == other.user

    def __ne__(self, other):
        return not self.__eq__(other)

    @set_required_scopes("user-library-read")
    async def contains_albums(self, *albums: Sequence[Union[str, Album]]) -> List[bool]:
        """Check if one or more albums is already saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        albums : Union[Album, str]
            A sequence of artist objects or spotify IDs
        """
        _albums = [str(obj) for obj in albums]
        return await self.user.http.is_saved_album(_albums)

    @set_required_scopes("user-library-read")
    async def contains_tracks(self, *tracks: Sequence[Union[str, Track]]) -> List[bool]:
        """Check if one or more tracks is already saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        tracks : Union[Track, str]
            A sequence of track objects or spotify IDs
        """
        _tracks = [str(obj) for obj in tracks]
        return await self.user.http.is_saved_track(_tracks)

    @set_required_scopes("user-library-read")
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

        return [Track(self.__client, item["track"]) for item in data["items"]]

    @set_required_scopes("user-library-read")
    async def get_all_tracks(self) -> List[Track]:
        """Get a list of all the songs saved in the current Spotify user’s ‘Your Music’ library.

        Returns
        -------
        tracks : List[:class:`Track`]
            The tracks of the artist.
        """
        tracks: List[Track] = []
        total = None
        offset = 0

        while True:
            data = await self.user.http.saved_tracks(limit=50, offset=offset)

            if total is None:
                total = data["total"]

            offset += 50
            tracks += list(
                Track(self.__client, item["track"]) for item in data["items"]
            )

            if len(tracks) >= total:
                break

        return tracks

    @set_required_scopes("user-library-read")
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

        return [Album(self.__client, item["album"]) for item in data["items"]]

    @set_required_scopes("user-library-read")
    async def get_all_albums(self) -> List[Album]:
        """Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        Returns
        -------
        albums : List[:class:`Album`]
            The albums.
        """
        albums: List[Album] = []
        total = None
        offset = 0

        while True:
            data = await self.user.http.saved_albums(limit=50, offset=offset)

            if total is None:
                total = data["total"]

            offset += 50
            albums += list(
                Album(self.__client, item["album"]) for item in data["items"]
            )

            if len(albums) >= total:
                break

        return albums

    @set_required_scopes("user-library-modify")
    async def remove_albums(self, *albums):
        """Remove one or more albums from the current user’s ‘Your Music’ library.

        Parameters
        ----------
        albums : Sequence[Union[Album, str]]
            A sequence of artist objects or spotify IDs
        """
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        await self.user.http.delete_saved_albums(",".join(_albums))

    @set_required_scopes("user-library-modify")
    async def remove_tracks(self, *tracks):
        """Remove one or more tracks from the current user’s ‘Your Music’ library.

        Parameters
        ----------
        tracks : Sequence[Union[Track, str]]
            A sequence of track objects or spotify IDs
        """
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        await self.user.http.delete_saved_tracks(",".join(_tracks))

    @set_required_scopes("user-library-modify")
    async def save_albums(self, *albums):
        """Save one or more albums to the current user’s ‘Your Music’ library.

        Parameters
        ----------
        albums : Sequence[Union[Album, str]]
            A sequence of artist objects or spotify IDs
        """
        _albums = [(obj if isinstance(obj, str) else obj.id) for obj in albums]
        await self.user.http.save_albums(",".join(_albums))

    @set_required_scopes("user-library-modify")
    async def save_tracks(self, *tracks):
        """Save one or more tracks to the current user’s ‘Your Music’ library.

        Parameters
        ----------
        tracks : Sequence[Union[Track, str]]
            A sequence of track objects or spotify IDs
        """
        _tracks = [(obj if isinstance(obj, str) else obj.id) for obj in tracks]
        await self.user.http.save_tracks(_tracks)
