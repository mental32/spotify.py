from functools import partial
from typing import Optional, List

from ..oauth import set_required_scopes
from . import AsyncIterable, URIBase, Image, Artist, Track


class Album(URIBase, AsyncIterable):  # pylint: disable=too-many-instance-attributes
    """A Spotify Album.

    Attributes
    ----------
    artists : List[Artist]
        The artists for the album.
    id : str
        The ID of the album.
    name : str
        The name of the album.
    href : str
        The HTTP API URL for the album.
    uri : str
        The URI for the album.
    album_group : str
        ossible values are “album”, “single”, “compilation”, “appears_on”.
        Compare to album_type this field represents relationship between the artist and the album.
    album_type : str
        The type of the album: one of "album" , "single" , or "compilation".
    release_date : str
        The date the album was first released.
    release_date_precision : str
        The precision with which release_date value is known: year, month or day.
    genres : List[str]
        A list of the genres used to classify the album.
    label : str
        The label for the album.
    popularity : int
        The popularity of the album. The value will be between 0 and 100, with 100 being the most popular.
    copyrights : List[Dict]
        The copyright statements of the album.
    markets : List[str]
        The markets in which the album is available: ISO 3166-1 alpha-2 country codes.
    """

    def __init__(self, client, data):
        self.__client = client

        # Simple object attributes.
        self.type = data.pop("album_type", None)
        self.group = data.pop("album_group", None)
        self.artists = [Artist(client, artist) for artist in data.pop("artists", [])]

        if self.artists:
            self.artist = self.artists[0]
        else:
            self.artist = None

        self.markets = data.pop("avaliable_markets", None)
        self.url = data.pop("external_urls").get("spotify", None)
        self.id = data.pop("id", None)  # pylint: disable=invalid-name
        self.name = data.pop("name", None)
        self.href = data.pop("href", None)
        self.uri = data.pop("uri", None)
        self.release_date = data.pop("release_date", None)
        self.release_date_precision = data.pop("release_date_precision", None)
        self.images = list(Image(**image) for image in data.pop("images", []))
        self.restrictions = data.pop("restrictions", None)

        # Full object attributes
        self.genres = data.pop("genres", None)
        self.copyrights = data.pop("copyrights", None)
        self.label = data.pop("label", None)
        self.popularity = data.pop("popularity", None)
        self.total_tracks = data.pop("total_tracks", None)

        # AsyncIterable attrs
        self.__aiter_klass__ = Track
        self.__aiter_fetch__ = partial(
            self.__client.http.album_tracks, self.id, limit=50
        )

    def __repr__(self):
        return f"<spotify.Album: {(self.name or self.id or self.uri)!r}>"

    # Public

    @set_required_scopes(None)
    async def get_tracks(
        self, *, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> List[Track]:
        """get the albums tracks from spotify.

        Parameters
        ----------
        limit : Optional[int]
            The limit on how many tracks to retrieve for this album (default is 20).
        offset : Optional[int]
            The offset from where the api should start from in the tracks.

        Returns
        -------
        tracks : List[Track]
            The tracks of the artist.
        """
        data = await self.__client.http.album_tracks(
            self.id, limit=limit, offset=offset
        )
        return list(Track(self.__client, item) for item in data["items"])

    @set_required_scopes(None)
    async def get_all_tracks(
        self, *, market: Optional[str] = "US"
    ) -> List[Track]:  # pylint: disable=unused-argument
        """loads all of the albums tracks, depending on how many the album has this may be a long operation.

        Parameters
        ----------
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.

        Returns
        -------
        tracks : List[:class:`spotify.Track`]
            The tracks of the artist.
        """
        return [track async for track in self]
