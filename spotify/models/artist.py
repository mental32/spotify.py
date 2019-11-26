from functools import partial
from typing import Optional, List, TYPE_CHECKING

from ..oauth import set_required_scopes
from . import AsyncIterable, URIBase, Image

if TYPE_CHECKING:
    import spotify


class Artist(URIBase, AsyncIterable):  # pylint: disable=too-many-instance-attributes
    """A Spotify Artist.

    Attributes
    ----------
    id : str
        The Spotify ID of the artist.
    uri : str
        The URI of the artist.
    url : str
        The open.spotify URL.
    href : str
        A link to the Web API endpoint providing full details of the artist.
    name : str
        The name of the artist.
    genres : List[str]
        A list of the genres the artist is associated with.
        For example: "Prog Rock" , "Post-Grunge". (If not yet classified, the array is empty.)
    followers : Optional[int]
        The total number of followers.
    popularity : int
        The popularity of the artist.
        The value will be between 0 and 100, with 100 being the most popular.
        The artist’s popularity is calculated from the popularity of all the artist’s tracks.
    images : List[Image]
        Images of the artist in various sizes, widest first.
    """

    def __init__(self, client, data):
        self.__client = client

        # Simplified object attributes
        self.id = data.pop("id")  # pylint: disable=invalid-name
        self.uri = data.pop("uri")
        self.url = data.pop("external_urls").get("spotify", None)
        self.href = data.pop("href")
        self.name = data.pop("name")

        # Full object attributes
        self.genres = data.pop("genres", None)
        self.followers = data.pop("followers", {}).get("total", None)
        self.popularity = data.pop("popularity", None)
        self.images = list(Image(**image) for image in data.pop("images", []))

        # AsyncIterable attrs
        from .album import Album

        self.__aiter_klass__ = Album
        self.__aiter_fetch__ = partial(
            self.__client.http.artist_albums, self.id, limit=50
        )

    def __repr__(self):
        return f"<spotify.Artist: {self.name!r}>"

    # Public

    @set_required_scopes(None)
    async def get_albums(
        self,
        *,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        include_groups=None,
        market: Optional[str] = None,
    ) -> List["spotify.Album"]:
        """Get the albums of a Spotify artist.

        Parameters
        ----------
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optiona[int]
            The offset of which Spotify should start yielding from.
        include_groups : INCLUDE_GROUPS_TP
            INCLUDE_GROUPS
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.

        Returns
        -------
        albums : List[Album]
            The albums of the artist.
        """
        from .album import Album

        data = await self.__client.http.artist_albums(
            self.id,
            limit=limit,
            offset=offset,
            include_groups=include_groups,
            market=market,
        )
        return list(Album(self.__client, item) for item in data["items"])

    @set_required_scopes(None)
    async def get_all_albums(self, *, market="US") -> List["spotify.Album"]:
        """loads all of the artists albums, depending on how many the artist has this may be a long operation.

        Parameters
        ----------
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.

        Returns
        -------
        albums : List[Album]
            The albums of the artist.
        """
        from .album import Album

        albums: List[Album] = []
        offset = 0
        total = await self.total_albums(market=market)

        while len(albums) < total:
            data = await self.__client.http.artist_albums(
                self.id, limit=50, offset=offset, market=market
            )

            offset += 50
            albums += list(Album(self.__client, item) for item in data["items"])

        return albums

    @set_required_scopes(None)
    async def total_albums(self, *, market: str = None) -> int:
        """get the total amout of tracks in the album.

        Parameters
        ----------
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.

        Returns
        -------
        total : int
            The total amount of albums.
        """
        data = await self.__client.http.artist_albums(
            self.id, limit=1, offset=0, market=market
        )
        return data["total"]

    @set_required_scopes(None)
    async def top_tracks(self, country: str = "US") -> List["spotify.Track"]:
        """Get Spotify catalog information about an artist’s top tracks by country.

        Parameters
        ----------
        country : str
            The country to search for, it defaults to 'US'.

        Returns
        -------
        tracks : List[Track]
            The artists top tracks.
        """
        from .track import Track

        top = await self.__client.http.artist_top_tracks(self.id, country=country)
        return list(Track(self.__client, item) for item in top["tracks"])

    @set_required_scopes(None)
    async def related_artists(self) -> List["Artist"]:
        """Get Spotify catalog information about artists similar to a given artist.

        Similarity is based on analysis of the Spotify community’s listening history.

        Returns
        -------
        artists : List[Artits]
            The artists deemed similar.
        """
        related = await self.__client.http.artist_related_artists(self.id)
        return list(Artist(self.__client, item) for item in related["artists"])
