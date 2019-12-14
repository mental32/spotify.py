import asyncio
from typing import Optional, List, Iterable, NamedTuple, Type, Union, Dict

from .http import HTTPClient
from .utils import to_id
from . import OAuth2, Artist, Album, Track, User, Playlist

__all__ = ("Client", "SearchResults")

_TYPES = {"artist": Artist, "album": Album, "playlist": Playlist, "track": Track}

_SEARCH_TYPES = {"track", "playlist", "artist", "album"}
_SEARCH_TYPE_ERR = (
    'Bad queary type! got "%s" expected any of: track, playlist, artist, album'
)


class SearchResults(NamedTuple):
    """A namedtuple of search results.

    Attributes
    ----------
    artists : List[:class:`Artist`]
        The artists of the search.
    playlists : List[:class:`Playlist`]
        The playlists of the search.
    albums : List[:class:`Album`]
        The albums of the search.
    tracks : List[:class:`Track`]
        The tracks of the search.
    """

    artists: Optional[List[Artist]] = None
    playlists: Optional[List[Playlist]] = None
    albums: Optional[List[Album]] = None
    tracks: Optional[List[Track]] = None


class Client:
    """Represents a Client app on Spotify.

    This class is used to interact with the Spotify API.

    Parameters
    ----------
    client_id : :class:`str`
        The client id provided by spotify for the app.
    client_secret : :class:`str`
        The client secret for the app.
    loop : Optional[:class:`asyncio.AbstractEventLoop`]
        The event loop the client should run on, if no loop is specified `asyncio.get_event_loop()` is called and used instead.

    Attributes
    ----------
    client_id : :class:`str`
        The applications client_id, also aliased as `id`
    http : :class:`HTTPClient`
        The HTTPClient that is being used.
    loop : Optional[:class:`asyncio.AbstractEventLoop`]
        The event loop the client is running on.
    """

    _default_http_client: Type[HTTPClient] = HTTPClient

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        if not isinstance(client_id, str):
            raise TypeError("client_id must be a string.")

        if not isinstance(client_secret, str):
            raise TypeError("client_secret must be a string.")

        if loop is not None and not isinstance(loop, asyncio.AbstractEventLoop):
            raise TypeError(
                "loop argument must be None or an instance of asyncio.AbstractEventLoop."
            )

        self.loop = loop = loop or asyncio.get_event_loop()
        self.http = self._default_http_client(client_id, client_secret, loop=loop)

    def __repr__(self):
        return f"<spotify.Client: {self.http.client_id!r}>"

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    # Properties

    @property
    def client_id(self) -> str:
        """:class:`str` - The Spotify client ID."""
        return self.http.client_id

    @property
    def id(self):  # pylint: disable=invalid-name
        """:class:`str` - The Spotify client ID."""
        return self.http.client_id

    # Public api

    def oauth2_url(
        self,
        redirect_uri: str,
        scopes: Optional[Union[Iterable[str], Dict[str, bool]]] = None,
        state: Optional[str] = None,
    ) -> str:
        """Generate an oauth2 url for user authentication.

        This is an alias to :meth:`OAuth2.url_only` but the
        difference is that the client id is autmatically
        passed in to the constructor.

        Parameters
        ----------
        redirect_uri : :class:`str`
            Where spotify should redirect the user to after authentication.
        scopes : Optional[Iterable[:class:`str`], Dict[:class:`str`, :class:`bool`]]
            The scopes to be requested.
        state : Optional[:class:`str`]
            Using a state value can increase your assurance that an incoming connection is the result of an
            authentication request.

        Returns
        -------
        url : :class:`str`
            The OAuth2 url.
        """
        return OAuth2.url_only(
            client_id=self.http.client_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            state=state,
        )

    async def close(self) -> None:
        """Close the underlying HTTP session to Spotify."""
        await self.http.close()

    async def user_from_token(self, token: str) -> User:
        """Create a user session from a token.

        .. note::

            This code is equivelent to `User.from_token(client, token)`

        Parameters
        ----------
        token : :class:`str`
            The token to attatch the user session to.

        Returns
        -------
        user : :class:`spotify.User`
            The user from the ID
        """
        return await User.from_token(self, token)

    async def get_album(self, spotify_id: str, *, market: str = "US") -> Album:
        """Retrive an album with a spotify ID.

        Parameters
        ----------
        spotify_id : :class:`str`
            The ID to search for.
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code

        Returns
        -------
        album : :class:`spotify.Album`
            The album from the ID
        """
        data = await self.http.album(to_id(spotify_id), market=market)
        return Album(self, data)

    async def get_artist(self, spotify_id: str) -> Artist:
        """Retrive an artist with a spotify ID.

        Parameters
        ----------
        spotify_id : str
            The ID to search for.

        Returns
        -------
        artist : Artist
            The artist from the ID
        """
        data = await self.http.artist(to_id(spotify_id))
        return Artist(self, data)

    async def get_track(self, spotify_id: str) -> Track:
        """Retrive an track with a spotify ID.

        Parameters
        ----------
        spotify_id : str
            The ID to search for.

        Returns
        -------
        track : Track
            The track from the ID
        """
        data = await self.http.track(to_id(spotify_id))
        return Track(self, data)

    async def get_user(self, spotify_id: str) -> User:
        """Retrive an user with a spotify ID.

        Parameters
        ----------
        spotify_id : str
            The ID to search for.

        Returns
        -------
        user : User
            The user from the ID
        """
        data = await self.http.user(to_id(spotify_id))
        return User(self, data)

    # Get multiple objects

    async def get_albums(self, *ids: str, market: str = "US") -> List[Album]:
        """Retrive multiple albums with a list of spotify IDs.

        Parameters
        ----------
        ids : List[str]
            the ID to look for
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code

        Returns
        -------
        albums : List[Album]
            The albums from the IDs
        """
        data = await self.http.albums(
            ",".join(to_id(_id) for _id in ids), market=market
        )
        return list(Album(self, album) for album in data["albums"])

    async def get_artists(self, *ids: str) -> List[Artist]:
        """Retrive multiple artists with a list of spotify IDs.

        Parameters
        ----------
        ids : List[:class:`str`]
            The IDs to look for.

        Returns
        -------
        artists : List[:class:`Artist`]
            The artists from the IDs
        """
        data = await self.http.artists(",".join(to_id(_id) for _id in ids))
        return list(Artist(self, artist) for artist in data["artists"])

    async def search(  # pylint: disable=invalid-name
        self,
        q: str,
        *,
        types: Iterable[str] = ("track", "playlist", "artist", "album"),
        limit: int = 20,
        offset: int = 0,
        market: str = "US",
        should_include_external: bool = False,
    ) -> SearchResults:
        """Access the spotify search functionality.

        >>> results = client.search('Cadet', types=['artist'])
        >>> for artist in result.get('artists', []):
        ...     if artist.name.lower() == 'cadet':
        ...         print(repr(artist))
        ...         break

        Parameters
        ----------
        q : :class:`str`
            the search query
        types : Optional[Iterable[`:class:`str`]]
            A sequence of search types (can be any of `track`, `playlist`, `artist` or `album`) to refine the search request.
            A `ValueError` may be raised if a search type is found that is not valid.
        limit : Optional[:class:`int`]
            The limit of search results to return when searching.
            Maximum limit is 50, any larger may raise a :class:`HTTPException`
        offset : Optional[:class:`int`]
            The offset from where the api should start from in the search results.
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.
        should_include_external : :class:`bool`
            If `True` is specified, the response will include any relevant audio content
            that is hosted externally. By default external content is filtered out from responses.

        Returns
        -------
        results : :class:`SearchResults`
            The results of the search.

        Raises
        ------
        TypeError
            Raised when a parameter with a bad type is passed.
        ValueError
            Raised when a bad search type is passed with the `types` argument.
        """
        if not hasattr(types, "__iter__"):
            raise TypeError("types must be an iterable.")

        types_ = set(types)

        if not types_.issubset(_SEARCH_TYPES):
            raise ValueError(_SEARCH_TYPE_ERR % types_.difference(_SEARCH_TYPES).pop())

        query_type = ",".join(tp.strip() for tp in types)

        include_external: Optional[str]
        if should_include_external:
            include_external = "audio"
        else:
            include_external = None

        data = await self.http.search(
            q=q,
            query_type=query_type,
            market=market,
            limit=limit,
            offset=offset,
            include_external=include_external,
        )

        return SearchResults(
            **{
                key: [_TYPES[obj["type"]](self, obj) for obj in value["items"]]
                for key, value in data.items()
            }
        )
