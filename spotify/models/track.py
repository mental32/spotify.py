"""Source implementation for spotify Tracks, and any other semantically relevent, implementation."""

import datetime
from itertools import starmap

from ..oauth import set_required_scopes
from . import URIBase, Image, Artist


class Track(URIBase):  # pylint: disable=too-many-instance-attributes
    """A Spotify Track object.

    Attribtues
    ----------
    id : :class:`str`
        The Spotify ID for the track.
    name : :class:`str`
        The name of the track.
    href : :class:`str`
        A link to the Web API endpoint providing full details of the track.
    uri : :class:`str`
        The Spotify URI for the track.
    duration : int
        The track length in milliseconds.
    explicit : bool
        Whether or not the track has explicit
        `True` if it does.
        `False` if it does not (or unknown)
    disc_number : int
        The disc number (usually 1 unless the album consists of more than one disc).
    track_number : int
        The number of the track.
        If an album has several discs, the track number is the number on the specified disc.
    url : :class:`str`
        The open.spotify URL for this Track
    is_local : bool
        Whether or not the track is from a local file.
    popularity : int
        POPULARITY
    preview_url : :class:`str`
        The preview URL for this Track.
    images : List[Image]
        The images of the Track.
    markets : List[:class:`str`]
        The available markets for the Track.
    """

    def __init__(self, client, data):
        from .album import Album

        self.__client = client

        self.artists = artists = list(
            Artist(client, artist) for artist in data.pop("artists", [])
        )
        self.artist = artists[-1] if artists else None

        album_ = data.pop("album", None)
        self.album = album = album_ and Album(client, album_)

        self.id = data.pop("id", None)  # pylint: disable=invalid-name
        self.name = data.pop("name", None)
        self.href = data.pop("href", None)
        self.uri = data.pop("uri", None)
        self.duration = data.pop("duration_ms", None)
        self.explicit = data.pop("explicit", None)
        self.disc_number = data.pop("disc_number", None)
        self.track_number = data.pop("track_number", None)
        self.url = data.pop("external_urls").get("spotify", None)
        self.is_local = data.pop("is_local", None)
        self.popularity = data.pop("popularity", None)
        self.preview_url = data.pop("preview_url", None)
        self.markets = data.pop("available_markets", [])

        if "images" in data:
            self.images = list(starmap(Image, data.pop("images")))
        else:
            self.images = album.images.copy()

    def __repr__(self):
        return f"<spotify.Track: {self.name!r}>"

    @set_required_scopes(None)
    def audio_analysis(self):
        """Get a detailed audio analysis for the track."""
        return self.__client.http.track_audio_analysis(self.id)

    @set_required_scopes(None)
    def audio_features(self):
        """Get audio feature information for the track."""
        return self.__client.http.track_audio_features(self.id)


class PlaylistTrack(Track, URIBase):
    """A Track on a Playlist.

    Like a regular :class:`Track` but has some additional attributes.

    Attributes
    ----------
    added_by : :class:`str`
        The Spotify user who added the track.
    is_local : bool
        Whether this track is a local file or not.
    added_at : datetime.datetime
        The datetime of when the track was added to the playlist.
    """

    __slots__ = ("added_at", "added_by", "is_local")

    def __init__(self, client, data):
        from .user import User

        super().__init__(client, data["track"])

        self.added_by = User(client, data["added_by"])
        self.added_at = datetime.datetime.strptime(
            data["added_at"], "%Y-%m-%dT%H:%M:%SZ"
        )
        self.is_local = data["is_local"]

    def __repr__(self):
        return f"<spotify.PlaylistTrack: {self.name!r}>"
