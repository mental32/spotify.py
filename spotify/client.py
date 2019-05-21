import asyncio
from typing import Optional, List, Iterable, Dict, Union

from .http import HTTPClient
from .utils import to_id
from . import (
    OAuth2,
    Artist,
    Album,
    Track,
    User,
    Playlist,
)

_TYPES = {
    'artist': Artist,
    'album': Album,
    'playlist': Playlist,
    'track': Track
}

_SEARCH_TYPES = {'track', 'playlist', 'artist', 'album'}
_SEARCH_TYPE_ERR = 'Bad queary type! got "%s" expected any of: track, playlist, artist, album'


class Client:
    """Represents a Client app on Spotify.

    This class is used to interact with the Spotify API.

    Parameters
    ----------
    client_id : str
        The client id provided by spotify for the app.
    client_secret : str
        The client secret for the app.
    loop : asyncio.AbstractEventLoop
        The event loop the client should run on, if no loop is specified `asyncio.get_event_loop()` is called and used instead.

    Attributes
    ----------
    client_id : str
        The applications client_id, also aliased as `id`
    http : HTTPClient
        The HTTPClient that is being used.
    loop : asyncio.AbstractEventLoop
        The event loop the client is running on.
    """
    _default_http_client = HTTPClient

    def __init__(self, client_id, client_secret, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.http = self._default_http_client(client_id, client_secret, loop=loop)

    def __repr__(self):
        return '<spotify.Client: "%s">' % self.http.client_id

    @property
    def client_id(self):
        return self.http.client_id

    @property
    def id(self):
        return self.http.client_id

    def oauth2_url(self, redirect_uri: str, scope: Optional[str] = None, state: Optional[str] = None) -> str:
        """Generate an outh2 url for user authentication.

        Parameters
        ----------
        redirect_uri : str
            Where spotify should redirect the user to after authentication.
        scope : Optional[str]
            Space seperated spotify scopes for different levels of access.
        state : Optional[str]
            Using a state value can increase your assurance that an incoming connection is the result of an authentication request.

        Returns
        -------
        url : str
            The OAuth2 url.
        """
        return OAuth2.url_(self.http.client_id, redirect_uri, scope=scope, state=state)

    async def close(self):
        """Close the underlying HTTP session to Spotify."""
        await self.http.close()

    async def user_from_token(self, token: str) -> User:
        """Create a user session from a token.

        This code is equivelent to `User.from_token(client, token)`

        Parameters
        ----------
        token : str
            The token to attatch the user session to.

        Returns
        -------
        user : User
            The user from the ID
        """
        return await User.from_token(self, token)

    async def get_album(self, spotify_id: str, *, market: str = 'US') -> Album:
        """Retrive an album with a spotify ID.

        Parameters
        ----------
        spotify_id : str
            The ID to search for.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code

        Returns
        -------
        album : Album
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

    async def get_albums(self, *ids: List[str], market: str = 'US') -> List[Album]:
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
        data = await self.http.albums(','.join(to_id(_id) for _id in ids), market=market)
        return list(Album(self, album) for album in data['albums'])

    async def get_artists(self, *ids: List[str]) -> List[Artist]:
        """Retrive multiple artists with a list of spotify IDs.

        Parameters
        ----------
        ids : List[str]
            the IDs to look for

        Returns
        -------
        artists : List[Artist]
            The artists from the IDs
        """
        data = await self.http.artists(','.join(to_id(_id) for _id in ids))
        return list(Artist(self, artist) for artist in data['artists'])

    async def search(self, q: str, *, types: Optional[Iterable[str]] = ['track', 'playlist', 'artist', 'album'], limit: Optional[int] = 20, offset: Optional[int] = 0, market: Optional[str] = None) -> Dict[str, List[Union[Track, Playlist, Artist, Album]]]:
        """Access the spotify search functionality.

        Parameters
        ----------
        q : str
            the search query
        types : Optional[Iterable[str]]
            A sequence of search types (can be any of `track`, `playlist`, `artist` or `album`) to refine the search request.
            A `ValueError` may be raised if a search type is found that is not valid.
        limit : Optional[int]
            The limit of search results to return when searching.
            Maximum limit is 50, any larger may raise a :class:`HTTPException`
        offset : Optional[int]
            The offset from where the api should start from in the search results.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking.

        Returns
        -------
        results : Dict[str, List[Union[Track, Playlist, Artist, Album]]]
            The results of the search.
        """
        if not hasattr(types, '__iter__'):
            raise TypeError('types must be an iterable.')

        elif not isinstance(types, list):
            types = list(item for item in types)

        types_ = set(types)

        if not types_.issubset(_SEARCH_TYPES):
            raise ValueError(_SEARCH_TYPE_ERR % types_.difference(_SEARCH_TYPES).pop())

        kwargs = {
            'q': q.replace(' ', '+'),
            'queary_type': ','.join(tp.strip() for tp in types),
            'market': market,
            'limit': limit,
            'offset': offset
        }

        data = await self.http.search(**kwargs)

        return {key: [_TYPES[obj['type']](self, obj) for obj in value['items']] for key, value in data.items()}
