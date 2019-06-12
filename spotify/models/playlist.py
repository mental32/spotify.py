from typing import List
from functools import partial

from . import SpotifyBase, URIBase, Track, PlaylistTrack, Image


class PartialTracks(SpotifyBase):
    """A partial track object which contains information about the tracks but not the tracks itself.

    Attributes
    ----------
    total : int
        The total amount of tracks.
    """
    __slots__ = ('total', '__func', '__iter', '__client')

    def __init__(self, client, data):
        self.total = data['total']
        self.__func = partial(client.http.request, ('GET', data['href']))
        self.__iter = None

    def __repr__(self):
        return '<spotify.PartialTracks: total="%s">' % self.total

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.__iter is None:
            self.__iter = iter((await self.__func())['items'])

        try:
            track = next(self.__iter)
        except StopIteration:
            raise StopAsyncIteration
        else:
            return PlaylistTrack(self.__client, track)

    async def build(self):
        """get the track object for each link in the partial tracks data

        Returns
        -------
        tracks : List[PlaylistTrack]
            The tracks
        """
        data = await self.__func()
        return list(PlaylistTrack(self.__client, track) for track in data['items'])


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
    tracks : Option[List[PlaylistTrack]]
        list of playlist track objects.
    """
    def __init__(self, client, data, *, http=None):
        from .user import User

        self.__client = client
        self.__http = http or client.http

        self.collaborative = data.pop('collaborative')
        self.description = data.pop('description', None)
        self.url = data.pop('external_urls').get('spotify', None)
        self.followers = data.pop('followers', {}).get('total', None)
        self.href = data.pop('href')
        self.id = data.pop('id')
        self.images = list(Image(**image) for image in data.pop('images', []))
        self.name = data.pop('name')
        self.owner = User(client, data=data.pop('owner'))
        self.uri = data.pop('uri')

        if 'next' in data['tracks']:  # Paging object.
            pass  # TODO: Support paging objects.
        else:
            self._tracks = tracks = PartialTracks(client, data.pop('tracks'))
            self.total_tracks = tracks.total

    def __repr__(self):
        return '<spotify.Playlist: "%s">' % (getattr(self, 'name', None) or self.id)

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
            data = await self.__http.get_playlist_tracks(self.owner.id, self.id, limit=50, offset=offset)

            _tracks += [PlaylistTrack(self.__client, item) for item in data['items']]
            offset += 50

        self.total_tracks = len(_tracks)
        return list(_tracks)
