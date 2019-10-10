from contextlib import asynccontextmanager
from itertools import islice
from typing import List, Optional, Union, Callable, Tuple

from ..http import HTTPUserClient
from . import URIBase, Track, PlaylistTrack, Image


class Playlist(URIBase):  # pylint: disable=too-many-instance-attributes
    """A Spotify Playlist.

    Attributes
    ----------
    collaborative : :class:`bool`
        Returns true if context is not search and the owner allows other users to modify the playlist. Otherwise returns false.
    description : :class:`str`
        The playlist description. Only returned for modified, verified playlists, otherwise null.
    url : :class:`str`
        The open.spotify URL.
    followers : :class:`int`
        The total amount of followers
    href : :class:`str`
        A link to the Web API endpoint providing full details of the playlist.
    id : :class:`str`
        The Spotify ID for the playlist.
    images : List[:class:`spotify.Image`]
        Images for the playlist.
        The array may be empty or contain up to three images.
        The images are returned by size in descending order.
        If returned, the source URL for the image ( url ) is temporary and will expire in less than a day.
    name : :class:`str`
        The name of the playlist.
    owner : :class:`spotify.User`
        The user who owns the playlist
    public : :class`bool`
        The playlist’s public/private status:
            true the playlist is public,
            false the playlist is private,
            null the playlist status is not relevant.
    snapshot_id : :class:`str`
        The version identifier for the current playlist.
    tracks : Optional[Tuple[:class:`PlaylistTrack`]]
        A tuple of :class:`PlaylistTrack` objects or `None`.
    """

    __slots__ = (
        "collaborative",
        "description",
        "url",
        "followers",
        "href",
        "id",
        "images",
        "name",
        "owner",
        "public",
        "uri",
        "total_tracks",
        "__client",
        "__http",
        "__tracks",
    )

    def __init__(
        self,
        client: "spotify.Client",
        data: Union[dict, "Playlist"],
        *,
        http: Optional[HTTPUserClient] = None,
    ):
        self.__client = client
        self.__http = http
        self.__tracks = None
        self.total_tracks = None

        if not isinstance(data, (Playlist, dict)):
            raise TypeError("data must be a Playlist instance or a dict.")

        if isinstance(data, dict):
            self.__from_raw(data)
        else:
            for name in filter((lambda name: name[0] != "_"), Playlist.__slots__):
                setattr(self, name, getattr(data, name))

    def __repr__(self):
        return f'<spotify.Playlist: {getattr(self, "name", None) or self.id}>'

    def __len__(self):
        return self.total_tracks

    # Internals

    def __from_raw(self, data: dict) -> None:
        from .user import User

        client = self.__client

        self.id = data.pop("id")  # pylint: disable=invalid-name

        self.images = tuple(Image(**image) for image in data.pop("images", []))
        self.owner = User(client, data=data.pop("owner"))

        self.public = data.pop("public")
        self.collaborative = data.pop("collaborative")
        self.description = data.pop("description", None)
        self.followers = data.pop("followers", {}).get("total", None)
        self.href = data.pop("href")
        self.name = data.pop("name")
        self.url = data.pop("external_urls").get("spotify", None)
        self.uri = data.pop("uri")

        self.__tracks = tracks = (
            tuple(PlaylistTrack(client, item) for item in data["tracks"]["items"])
            if "items" in data["tracks"]
            else None
        )

        self.total_tracks = (
            len(tracks) if tracks is not None else data["tracks"]["total"]
        )

    @asynccontextmanager
    async def __mutate_tracks(self):
        if self.tracks is None:
            self.__tracks = await self.get_all_tracks()

        tracks = list(self.tracks)
        prev_len = len(tracks)

        yield tracks

        if not prev_len and not len(tracks):
            # the tracks were empty and is still empty.
            # skip the api call.
            return

        await self.replace_tracks(*tracks)
        self.__tracks = tuple(tracks)

    # Properties

    @property
    def tracks(self):
        return self.__tracks

    # Track retrieval

    async def get_tracks(
        self, *, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> Tuple[PlaylistTrack]:
        """Get a fraction of a playlists tracks.

        Parameters
        ----------
        limit : Optional[int]
            The limit on how many tracks to retrieve for this playlist (default is 20).
        offset : Optional[int]
            The offset from where the api should start from in the tracks.

        Returns
        -------
        tracks : Tuple[PlaylistTrack]
            The tracks of the playlist.
        """
        data = self.__http.get_playlist_tracks(self.id, limit=limit, offset=offset)
        return tuple(PlaylistTrack(self.__client, item) for item in data["items"])

    async def get_all_tracks(self) -> Tuple[PlaylistTrack]:
        """Get all playlist tracks from the playlist.

        Returns
        -------
        tracks : Tuple[:class:`PlaylistTrack`]
            The playlists tracks.
        """
        _tracks = []
        offset = 0
        while len(_tracks) < self.total_tracks:
            data = await self.__http.get_playlist_tracks(
                self.id, limit=50, offset=offset
            )

            _tracks += [PlaylistTrack(self.__client, item) for item in data["items"]]
            offset += 50

        self.total_tracks = len(_tracks)
        return tuple(_tracks)

    # Playlist structure modification

    # Basic api wrapping

    async def add_tracks(self, *tracks) -> str:
        """Add one or more tracks to a user’s playlist.

        Parameters
        ----------
        tracks : Iterable[Union[:class:`str`, :class:`Track`]]
            Tracks to add to the playlist

        Returns
        -------
        snapshot_id : :class:`str`
            The snapshot id of the playlist.
        """
        data = await self.__http.add_playlist_tracks(
            self.id, tracks=[str(track) for track in tracks]
        )
        return data["snapshot_id"]

    async def remove_tracks(self, *tracks):
        """Remove one or more tracks from a user’s playlist.

        Parameters
        ----------
        tracks : Iterable[Union[:class:`str`, :class:`Track`]]
            Tracks to remove from the playlist

        Returns
        -------
        snapshot_id : :class:`str`
            The snapshot id of the playlist.
        """
        data = await self.__http.remove_playlist_tracks(
            self.id, tracks=[str(track) for track in tracks]
        )
        return data["snapshot_id"]

    async def replace_tracks(self, *tracks) -> str:
        """Replace all the tracks in a playlist, overwriting its existing tracks.

        This powerful request can be useful for replacing tracks, re-ordering existing tracks, or clearing the playlist.

        Parameters
        ----------
        tracks : Iterable[Union[:class:`str`, :class:`Track`]]
            Tracks to place in the playlist
        """
        if not isinstance(tracks, (list, tuple)):
            tracks = list(*tracks)

        bucket = []
        for track in tracks:
            if not isinstance(track, (str, Track)):
                raise TypeError(
                    f"tracks must be a iterable of strings or Track instances. Got {type(track)!r}"
                )

            bucket.append(str(track))

        tracks = tuple(bucket)

        if len(tracks) <= 100:
            head, tracks = tracks, []
        else:
            head, tracks = tracks[:100], tracks[100:]

        await self.__http.replace_playlist_tracks(self.id, tracks=head)

        while tracks:
            head, tracks = tracks[:100], tracks[100:]
            await self.extend(head)

    async def reorder_tracks(
        self,
        start: int,
        insert_before: int,
        length: int = 1,
        *,
        snapshot_id: Optional[str] = None,
    ) -> str:
        """Reorder a track or a group of tracks in a playlist.

        Parameters
        ----------
        start : int
            The position of the first track to be reordered.
        insert_before : int
            The position where the tracks should be inserted.
        length : Optional[int]
            The amount of tracks to be reordered. Defaults to 1 if not set.
        snapshot_id : str
            The playlist’s snapshot ID against which you want to make the changes.

        Returns
        -------
        snapshot_id : str
            The snapshot id of the playlist.
        """
        data = await self.__http.reorder_playlists_tracks(
            self.id, start, length, insert_before, snapshot_id=snapshot_id
        )
        return data["snapshot_id"]

    # Library functionality.

    async def clear(self):
        """Clear the playlists tracks.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.

        .. warning::

            This is a desctructive operation and can not be reversed!
        """
        await self.__http.replace_playlist_tracks(self.id, tracks=[])

    async def extend(self, tracks: Union["Playlist", List[Union[Track, str]]]):
        """Extend a playlists tracks with that of another playlist or a list of Track/Track URIs.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.

        Parameters
        ----------
        tracks : Union["Playlist", List[Union[Track, str]]]
            Tracks to add to the playlist, acceptable values are:
             - A :class:`spotify.Playlist` object
             - A :class:`list` of :class:`spotify.Track` objects or Track URIs

        Returns
        -------
        snapshot_id : str
            The snapshot id of the playlist.
        """
        if isinstance(tracks, Playlist):
            tracks = await tracks.get_all_tracks()

        elif not isinstance(tracks, (list, tuple)):
            raise TypeError(
                f"`tracks` was an invalid type, expected any of: Playlist, List[Union[Track, str]], instead got {type(tracks)}"
            )

        tracks = (str(track) for track in tracks)

        while True:
            head = list(islice(tracks, 0, 100))

            if not head:
                break

            await self.__http.add_playlist_tracks(self.id, tracks=head)

    async def insert(self, index, obj: Union[PlaylistTrack, Track]) -> None:
        """Insert an object before the index.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.
        """
        if not isinstance(obj, (PlaylistTrack, Track)):
            raise TypeError(
                f"Expected a PlaylistTrack or Track object instead got {obj!r}"
            )

        async with self.__mutate_tracks() as tracks:
            tracks.insert(index, obj)

    async def pop(self, index: int = -1) -> PlaylistTrack:
        """Remove and return the track at the specified index.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.

        Returns
        -------
        playlist_track : :class:`PlaylistTrack`
            The track that was removed.

        Raises
        ------
        IndexError
            If there are no tracks or the index is out of range.
        """
        async with self.__mutate_tracks() as tracks:
            return tracks.pop(index)

    async def sort(
        self,
        *,
        key: Optional[Callable[[PlaylistTrack], bool]] = None,
        reverse: Optional[bool] = False,
    ) -> None:
        """Stable sort the playlist in place.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.
        """
        async with self.__mutate_tracks() as tracks:
            tracks.sort(key=key, reverse=reverse)

    async def remove(self, value: Union[PlaylistTrack, Track]) -> None:
        """Remove the first occurence of the value.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.

        Raises
        -------
        ValueError
            If the value is not present.
        """
        async with self.__mutate_tracks() as tracks:
            tracks.remove(value)

    async def copy(self) -> "Playlist":
        """Return a shallow copy of the playlist object.

        Returns
        -------
        playlist : :class:`Playlist`
            The playlist object copy.
        """
        return Playlist(client=self.__client, data=self, http=self.__http)

    async def reverse(self) -> None:
        """Reverse the playlist in place.

        .. note::

            This method will mutate the current
            playlist object, and the spotify Playlist.
        """
        async with self.__mutate_tracks() as tracks:
            tracks.reverse()
