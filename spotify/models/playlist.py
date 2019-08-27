from functools import partial
from itertools import islice
from typing import List, Optional, Union

from . import SpotifyBase, URIBase, Track, PlaylistTrack, Image


class PartialTracks(SpotifyBase):
    """A partial track object which contains information about the tracks but not the tracks itself.

    Attributes
    ----------
    total : int
        The total amount of tracks.
    """

    __slots__ = ("total", "__func", "__iter", "__client")

    def __init__(self, client, data):
        self.total = data["total"]
        self.__func = partial(client.http.request, ("GET", data["href"]))
        self.__iter = None

    def __repr__(self):
        return f"<spotify.PartialTracks: total={self.total!r}>"

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.__iter is None:
            self.__iter = iter((await self.__func())["items"])

        try:
            track = next(self.__iter)
        except StopIteration:
            raise StopAsyncIteration
        else:
            return PlaylistTrack(self.__client, track)

    async def build(self) -> List[PlaylistTrack]:
        """get the track object for each link in the partial tracks data.

        Returns
        -------
        tracks : List[PlaylistTrack]
            The tracks
        """
        data = await self.__func()
        return list(PlaylistTrack(self.__client, track) for track in data["items"])


class Playlist(URIBase):
    """A Spotify Playlist.

    Attributes
    ----------
    collaborative : bool
        Returns true if context is not search and the owner allows other users to modify the playlist. Otherwise returns false.
    description : str
        The playlist description. Only returned for modified, verified playlists, otherwise null.
    url : str
        The open.spotify URL.
    followers : int
        The total amount of followers
    href : str
        A link to the Web API endpoint providing full details of the playlist.
    id : str
        The Spotify ID for the playlist.
    images : List[Image]
        Images for the playlist.
        The array may be empty or contain up to three images.
        The images are returned by size in descending order.
        If returned, the source URL for the image ( url ) is temporary and will expire in less than a day.
    name : str
        The name of the playlist.
    owner : User
        The user who owns the playlist
    public : bool
        The playlist’s public/private status:
            true the playlist is public,
            false the playlist is private,
            null the playlist status is not relevant.
    snapshot_id : str
        The version identifier for the current playlist.
    tracks : Optional[List[PlaylistTrack]]
        list of playlist track objects.
    """

    def __init__(self, client, data, *, http=None):
        from .user import User

        self.__client = client
        self.__http = http or client.http

        self.collaborative = data.pop("collaborative")
        self.description = data.pop("description", None)
        self.url = data.pop("external_urls").get("spotify", None)
        self.followers = data.pop("followers", {}).get("total", None)
        self.href = data.pop("href")
        self.id = data.pop("id")
        self.images = list(Image(**image) for image in data.pop("images", []))
        self.name = data.pop("name")
        self.owner = User(client, data=data.pop("owner"))
        self.uri = data.pop("uri")

        if "next" in data["tracks"]:  # Paging object.
            pass  # TODO: Support paging objects.
        else:
            self._tracks = tracks = PartialTracks(client, data.pop("tracks"))
            self.total_tracks = tracks.total

    def __repr__(self):
        return '<spotify.Playlist: "%s">' % (getattr(self, "name", None) or self.id)

    # Track retrieval

    async def get_tracks(
        self, *, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> List[PlaylistTrack]:
        """Get a fraction of a playlists tracks.

        Parameters
        ----------
        limit : Optional[int]
            The limit on how many tracks to retrieve for this playlist (default is 20).
        offset : Optional[int]
            The offset from where the api should start from in the tracks.

        Returns
        -------
        tracks : List[PlaylistTrack]
            The tracks of the playlist.
        """
        data = self.__http.get_playlist_tracks(self.id, limit=limit, offset=offset)
        return list(PlaylistTrack(self.__client, item) for item in data["items"])

    async def get_all_tracks(self) -> List[PlaylistTrack]:
        """Get all playlist tracks from the playlist.

        Returns
        -------
        tracks : List[PlaylistTrack]
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
        return list(_tracks)

    # Playlist structure modification

    async def add_tracks(self, *tracks) -> str:
        """Add one or more tracks to a user’s playlist.

        Parameters
        ----------
        tracks : Sequence[Union[str, Track]]
            Tracks to add to the playlist

        Returns
        -------
        snapshot_id : str
            The snapshot id of the playlist.
        """
        data = await self.__http.add_playlist_tracks(
            self.id, tracks=(str(track) for track in tracks)
        )
        return data["snapshot_id"]

    async def replace_tracks(self, *tracks) -> str:
        """Replace all the tracks in a playlist, overwriting its existing tracks.

        This powerful request can be useful for replacing tracks, re-ordering existing tracks, or clearing the playlist.

        Parameters
        ----------
        tracks : Sequence[Union[str, Track]]
            Tracks to place in the playlist
        """
        if not isinstance(tracks, (list, tuple)):
            tracks = list(*tracks)

        if len(tracks) <= 100:
            head = tracks
        else:
            head.tracks = tracks[:100], tracks[100:]

        await self.__http.replace_playlist_tracks(
            self.id, tracks=(str(track) for track in head)
        )

        while tracks:
            head.tracks = tracks[:100], tracks[100:]
            await self.extend_tracks(head)

    async def clear_tracks(self):
        """Clear the playlists tracks.

        .. warning::

            This is a desctructive operation and is very hard to reverse!
        """
        await self.__http.replace_playlist_tracks(self.id, tracks=[])

    async def remove_tracks(self, *tracks):
        """Remove one or more tracks from a user’s playlist.

        Parameters
        ----------
        tracks : Sequence[Union[str, Track]]
            Tracks to remove from the playlist

        Returns
        -------
        snapshot_id : str
            The snapshot id of the playlist.
        """
        data = await self.__http.remove_playlist_tracks(
            self.id, tracks=(str(track) for track in tracks)
        )
        return data["snapshot_id"]

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

    async def extend_tracks(
        self, tracks: Union["Playlist", PartialTracks, List[Union[Track, str]]]
    ):
        """Extend a playlists tracks with that of another playlist, PartialTracks or a list of Track/Track URIs.

        Parameters
        ----------
        tracks : Union[Playlist, PartialTracks, List[Union[Track, str]]]
            Tracks to add to the playlist, acceptable values are:
             - A :class:`spotify.Playlist` object
             - A :class:`spotify.models.PartialTracks` object
             - A :class:`list` of :class:`spotify.Track` objects or Track URIs

        Returns
        -------
        snapshot_id : str
            The snapshot id of the playlist.
        """
        if isinstance(tracks, Playlist):
            tracks = await tracks.get_all_tracks()

        elif isinstance(tracks, PartialTracks):
            tracks = await tracks.build()

        elif not isinstance(tracks, (list, tuple)):
            raise TypeError(
                f"`tracks` was an invalid type, expected any of: Playlist, PartialTracks, List[Union[Track, str]], instead got {type(tracks)}"
            )

        tracks = (str(track) for track in tracks)

        while True:
            head = list(islice(tracks, 0, 100))

            if not head:
                break

            data = await self.__http.add_playlist_tracks(self.id, tracks=head)
