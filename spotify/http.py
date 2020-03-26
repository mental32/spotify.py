# pylint: skip-file

import asyncio
import sys
import json
import time
from typing import (
    Optional,
    List,
    Sequence,
    Union,
    Dict,
    Awaitable,
    BinaryIO,
    Tuple,
    Any,
)
from base64 import b64encode
from urllib.parse import quote

import aiohttp
import backoff  # type: ignore

from . import __version__
from .utils import filter_items
from .errors import (
    HTTPException,
    Forbidden,
    NotFound,
    SpotifyException,
    BearerTokenError,
    RateLimitedException,
)

__all__ = ("HTTPClient", "HTTPUserClient")

_GET_BEARER_ARG_ERR = "{name} was `None` when getting a bearer token."
_PYTHON_VERSION = ".".join(str(_) for _ in sys.version_info[:3])
_AIOHTTP_VERSION = aiohttp.__version__


class HTTPClient:
    """A class responsible for handling all HTTP logic.

    This class combines a small amount of stateful logic control
    with the :meth:`request` method and a very thin wrapper over
    the raw HTTP API.

    All endpoint methods mirror the default arguments the API
    uses and is best described as a series of "good defaults"
    for the routes.

    Parameters
    ----------
    client_id : str
        The client id provided by spotify for the app.
    client_secret : str
        The client secret for the app.
    loop : Optional[event loop]
        The event loop the client should run on, if no loop is specified `asyncio.get_event_loop()` is called and used instead.


    Attributes
    ----------
    loop : AbstractEventLoop
        The loop the client is running with.
    client_id : str
        The client id of the app.
    client_secret : str
        The client secret.
    """

    RETRY_AMOUNT = 10
    DEFAULT_USER_AGENT = (
        user_agent
    ) = f"Application (https://github.com/mental32/spotify.py {__version__}) Python/{_PYTHON_VERSION} aiohttp/{_AIOHTTP_VERSION}"

    def __init__(self, client_id: str, client_secret: str, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._session = aiohttp.ClientSession(loop=self.loop)

        self.client_id = client_id
        self.client_secret = client_secret

        self.bearer_info: Optional[Dict[str, str]] = None

        self.__request_barrier_lock = asyncio.Lock()
        self.__request_barrier = asyncio.Event()
        self.__request_barrier.set()

    @staticmethod
    def route(
        method: str, path: str, *, base: str = "https://api.spotify.com/v1", **kwargs
    ) -> Tuple[str, str]:
        """Used for constructing URLs for API endpoints.

        Parameters
        ----------
        method : str
            The HTTP/REST method used.
        path : str
            A path to be formatted.
        kwargs : Any
            The arguments used to format the path.

        Returns
        -------
        route : Tuple[str, str]
            A tuple of the method and formatted url path to use.
        """
        url = base + path

        if kwargs:
            url = url.format(
                **{
                    key: (quote(value) if isinstance(value, str) else value)
                    for key, value in kwargs.items()
                }
            )

        return (method, url)

    async def get_bearer_info(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """Get the application bearer token from client_id and client_secret.

        Raises
        ------
        SpotifyException
            This will be raised when either `client_id` or
            `client_secret` is `None`
        """
        client_id = client_id or self.client_id
        client_secret = client_secret or self.client_secret

        if client_id is None:
            raise SpotifyException(_GET_BEARER_ARG_ERR.format(name="client_id"))

        if client_secret is None:
            raise SpotifyException(_GET_BEARER_ARG_ERR.format(name="client_secret"))

        token = b64encode(":".join((client_id, client_secret)).encode())

        data = {"grant_type": "client_credentials"}
        headers = {"Authorization": f"Basic {token.decode()}"}

        session = session or self._session

        async with session.post(
            "https://accounts.spotify.com/api/token", data=data, headers=headers
        ) as response:
            bearer_info = json.loads(await response.text(encoding="utf-8"))

            if "error" in bearer_info.keys():
                raise BearerTokenError(response=response, message=bearer_info)

        return bearer_info

    @backoff.on_exception(backoff.expo, RateLimitedException)
    async def request(self, route, **kwargs):
        r"""Make a request to the spotify API with the current bearer credentials.

        Parameters
        ----------
        route : Tuple[str, str]
            A tuple of the method and url gained from :meth:`route`.
        \*\*kwargs : Any
            keyword arguments to pass into :class:`aiohttp.ClientSession.request`
        """
        assert isinstance(route, tuple), "route parameter was not a tuple!"
        assert len(route) == 2, "route parameter must have exactly two items"

        method, url, = route

        headers = kwargs.pop("headers", {})
        if "Authorization" not in headers:
            if self.bearer_info is None:
                self.bearer_info = bearer_info = await self.get_bearer_info()
                access_token = bearer_info["access_token"]
            else:
                access_token = self.bearer_info["access_token"]

            headers["Authorization"] = "Bearer " + access_token

        headers = {
            "Content-Type": kwargs.pop("content_type", "application/json"),
            "User-Agent": self.user_agent,
            **headers,
        }

        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
            kwargs["data"] = json.dumps(
                kwargs.pop("json"), separators=(",", ":"), ensure_ascii=True
            )

        for current_retry in range(self.RETRY_AMOUNT):
            await self.__request_barrier.wait()

            response = await self._session.request(
                method, url, headers=headers, **kwargs
            )

            try:
                status = response.status

                try:
                    data = json.loads(await response.text(encoding="utf-8"))
                except json.decoder.JSONDecodeError:
                    data = {}

                if 300 > status >= 200:
                    return data

                if status == 401:
                    self.bearer_info = bearer_info = await self.get_bearer_info()
                    headers["Authorization"] = "Bearer " + bearer_info["access_token"]
                    continue

                if status == 429:
                    # we're being rate limited.

                    self.__request_barrier.clear()
                    amount = int(response.headers.get("Retry-After"))
                    checkpoint = int(time.time())

                    async with self.__request_barrier_lock:
                        if (int(time.time()) - checkpoint) < amount:
                            self.__request_barrier.clear()
                            await asyncio.sleep(int(amount), loop=self.loop)
                            self.__request_barrier.set()

                    continue

                if status in (502, 503):
                    # unconditional retry
                    continue

                if status == 403:
                    raise Forbidden(response, data)

                if status == 404:
                    raise NotFound(response, data)
            finally:
                await response.release()

        if response.status == 429:
            raise RateLimitedException((amount, _max_retries - current_retry))

        raise HTTPException(response, data)

    async def close(self):
        """Close the underlying HTTP session."""
        await self._session.close()

    # Methods are defined in the order that they are listed in
    # the api docs (https://developer.spotify.com/documentation/web-api/reference/)

    # Album related endpoints

    def album(self, spotify_id: str, market: Optional[str] = "US") -> Awaitable:
        """Get Spotify catalog information for a single album.

        Parameters
        ----------
        spotify_id : str
            The spotify_id to search by.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.
        """
        route = self.route("GET", "/albums/{spotify_id}", spotify_id=spotify_id)
        payload: Dict[str, Any] = {}

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def album_tracks(
        self,
        spotify_id: str,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        market="US",
    ) -> Awaitable:
        """Get Spotify catalog information about an album’s tracks.

        Parameters
        ----------
        spotify_id : str
            The spotify_id to search by.
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optiona[int]
            The offset of which Spotify should start yielding from.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.
        """
        route = self.route("GET", "/albums/{spotify_id}/tracks", spotify_id=spotify_id)
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def albums(self, spotify_ids, market="US") -> Awaitable:
        """Get Spotify catalog information for multiple albums identified by their Spotify IDs.

        Parameters
        ----------
        spotify_ids : List[str]
            The spotify_ids to search by.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.
        """
        route = self.route("GET", "/albums/")
        payload: Dict[str, Any] = {"ids": spotify_ids}

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    # Artist related endpoints.

    def artist(self, spotify_id) -> Awaitable:
        """Get Spotify catalog information for a single artist identified by their unique Spotify ID.

        Parameters
        ----------
        spotify_id : str
            The spotify_id to search by.
        """
        route = self.route("GET", "/artists/{spotify_id}", spotify_id=spotify_id)
        return self.request(route)

    def artist_albums(
        self,
        spotify_id,
        include_groups=None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        market="US",
    ):
        """Get Spotify catalog information about an artist’s albums.

        Parameters
        ----------
        spotify_id : str
            The spotify_id to search by.
        include_groups : INCLUDE_GROUPS_TP
            INCLUDE_GROUPS
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optiona[int]
            The offset of which Spotify should start yielding from.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.
        """
        route = self.route("GET", "/artists/{spotify_id}/albums", spotify_id=spotify_id)
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if include_groups:
            payload["include_groups"] = include_groups

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def artist_top_tracks(self, spotify_id, country) -> Awaitable:
        """Get Spotify catalog information about an artist’s top tracks by country.

        Parameters
        ----------
        spotify_id : str
            The spotify_id to search by.
        country : COUNTRY_TP
            COUNTRY
        """
        route = self.route(
            "GET", "/artists/{spotify_id}/top-tracks", spotify_id=spotify_id
        )
        payload: Dict[str, Any] = {"country": country}
        return self.request(route, params=payload)

    def artist_related_artists(self, spotify_id) -> Awaitable:
        """Get Spotify catalog information about artists similar to a given artist.

        Similarity is based on analysis of the Spotify community’s listening history.

        Parameters
        ----------
        spotify_id : str
            The spotify_id to search by.
        """
        route = self.route(
            "GET", "/artists/{spotify_id}/related-artists", spotify_id=spotify_id
        )
        return self.request(route)

    def artists(self, spotify_ids) -> Awaitable:
        """Get Spotify catalog information for several artists based on their Spotify IDs.

        Parameters
        ----------
        spotify_id : List[str]
            The spotify_ids to search with.
        """
        route = self.route("GET", "/artists")
        payload: Dict[str, Any] = {"ids": spotify_ids}
        return self.request(route, params=payload)

    # Browse endpoints.

    def category(self, category_id, country=None, locale=None) -> Awaitable:
        """Get a single category used to tag items in Spotify (on, for example, the Spotify player’s “Browse” tab).

        Parameters
        ----------
        category_id : str
            The Spotify category ID for the category.
        country : COUNTRY_TP
            COUNTRY
        locale : LOCALE_TP
            LOCALE
        """
        route = self.route(
            "GET", "/browse/categories/{category_id}", category_id=category_id
        )
        payload: Dict[str, Any] = {}

        if country:
            payload["country"] = country

        if locale:
            payload["locale"] = locale

        return self.request(route, params=payload)

    def category_playlists(
        self,
        category_id,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        country=None,
    ) -> Awaitable:
        """Get a list of Spotify playlists tagged with a particular category.

        Parameters
        ----------
        category_id : str
            The Spotify category ID for the category.
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first item to return. Default: 0
        country : COUNTRY_TP
            COUNTRY
        """
        route = self.route(
            "GET", "/browse/categories/{category_id}/playlists", category_id=category_id
        )
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if country:
            payload["country"] = country

        return self.request(route, params=payload)

    def categories(
        self,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        country=None,
        locale=None,
    ) -> Awaitable:
        """Get a list of categories used to tag items in Spotify (on, for example, the Spotify player’s “Browse” tab).

        Parameters
        ----------
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first item to return. Default: 0
        country : COUNTRY_TP
            COUNTRY
        locale : LOCALE_TP
            LOCALE
        """
        route = self.route("GET", "/browse/categories")
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if country:
            payload["country"] = country

        if locale:
            payload["locale"] = locale

        return self.request(route, params=payload)

    def featured_playlists(
        self,
        locale=None,
        country=None,
        timestamp=None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ):
        """Get a list of Spotify featured playlists (shown, for example, on a Spotify player’s ‘Browse’ tab).

        Parameters
        ----------
        locale : LOCALE_TP
            LOCALE
        country : COUNTRY_TP
            COUNTRY
        timestamp : TIMESTAMP_TP
            TIMESTAMP
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first item to return. Default: 0
        """
        route = self.route("GET", "/browse/featured-playlists")
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if country:
            payload["country"] = country

        if locale:
            payload["locale"] = locale

        if timestamp:
            payload["timestamp"] = timestamp

        return self.request(route, params=payload)

    def new_releases(
        self, *, country=None, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> Awaitable:
        """Get a list of new album releases featured in Spotify (shown, for example, on a Spotify player’s “Browse” tab).

        Parameters
        ----------
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first item to return. Default: 0
        country : COUNTRY_TP
            COUNTRY
        """
        route = self.route("GET", "/browse/new-releases")
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if country:
            payload["country"] = country

        return self.request(route, params=payload)

    def recommendations(
        self,
        seed_artists,
        seed_genres,
        seed_tracks,
        *,
        limit: Optional[int] = 20,
        market=None,
        **filters,
    ):
        """Get Recommendations Based on Seeds.

        Parameters
        ----------
        seed_artists : str
            A comma separated list of Spotify IDs for seed artists. Up to 5 seed values may be provided.
        seed_genres : str
            A comma separated list of any genres in the set of available genre seeds. Up to 5 seed values may be provided.
        seed_tracks : str
            A comma separated list of Spotify IDs for a seed track. Up to 5 seed values may be provided.
        limit : Optional[int]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.
        max_* : Optional[Keyword arguments]
            For each tunable track attribute, a hard ceiling on the selected track attribute’s value can be provided.
        min_* : Optional[Keyword arguments]
            For each tunable track attribute, a hard floor on the selected track attribute’s value can be provided.
        target_* : Optional[Keyword arguments]
            For each of the tunable track attributes (below) a target value may be provided.
        """
        route = self.route("GET", "/recommendations")
        payload: Dict[str, Any] = {
            "seed_artists": seed_artists,
            "seed_genres": seed_genres,
            "seed_tracks": seed_tracks,
            "limit": limit,
        }

        if market:
            payload["market"] = market

        if filters:
            payload.update(filters)

        return self.request(route, params=payload)

    # Follow related endpoints.

    def following_artists_or_users(self, ids, *, type_="artist") -> Awaitable:
        """Check to see if the current user is following one or more artists or other Spotify users.

        Parameters
        ----------
        ids : List[:class:`str`]
            A comma-separated list of the artist or the user Spotify IDs to check.
            A maximum of 50 IDs can be sent in one request.
        type_ : Optional[:class:`str`]
            The ID type: either "artist" or "user".
            Default: "artist"
        """
        route = self.route("GET", "/me/following/contains")
        payload: Dict[str, Any] = {"ids": ids, "type": type_}

        return self.request(route, params=payload)

    def following_playlists(self, playlist_id: str, ids: List[str]) -> Awaitable:
        """Check to see if one or more Spotify users are following a specified playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID of the playlist.
        ids : List[:class:`str`]
            A list of the artist or the user Spotify IDs.
            A maximum of five IDs are allowed.
        """
        route = self.route(
            "GET",
            "/playlists/{playlist_id}/followers/contains",
            playlist_id=playlist_id,
        )
        payload: Dict[str, Any] = {"ids": ids}

        return self.request(route, params=payload)

    def follow_artist_or_user(self, type_: str, ids: List[str]) -> Awaitable:
        """Add the current user as a follower of one or more artists or other Spotify users.

        Parameters
        ----------
        type_ : :class:`str`
            either artist or user.
        ids : List[:class:`str`]
            A list of the artist or the user Spotify IDs.
        """
        route = self.route("PUT", "/me/following")
        payload: Dict[str, Any] = {"ids": ids, "type": type_}

        return self.request(route, params=payload)

    def followed_artists(
        self, *, limit: Optional[int] = 20, after: Optional[str] = None
    ) -> Awaitable:
        """Get the current user’s followed artists.

        Parameters
        ----------
        limit : Optional[:class:`int`]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        after : Optional[:class:`str`]
            The last artist ID retrieved from the previous request.
        """
        route = self.route("GET", "/me/following")
        payload: Dict[str, Any] = {"limit": limit, "type": "artist"}

        if after:
            payload["after"] = after

        return self.request(route, params=payload)

    def unfollow_artists_or_users(self, type_: str, ids: List[str]) -> Awaitable:
        """Remove the current user as a follower of one or more artists or other Spotify users.

        Parameters
        ----------
        type_ : :class:`str`
            either artist or user.
        ids : List[:class:`str`]
            A list of the artist or the user Spotify IDs.
        """
        route = self.route("DELETE", "/me/following")
        payload: Dict[str, Any] = {"ids": ids, "type": type_}

        return self.request(route, params=payload)

    def unfollow_playlist(self, playlist_id: str) -> Awaitable:
        """Remove the current user as a follower of a playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID of the playlist that is to be no longer followed.
        """
        route = self.route(
            "DELETE", "/playlists/{playlist_id}/followers", playlist_id=playlist_id
        )

        return self.request(route)

    def is_saved_album(self, ids) -> Awaitable:
        """Check if one or more albums is already saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        ids : List[:class:`str`]
            A list of the Spotify IDs.
        """
        route = self.route("GET", "/me/albums/contains")
        payload: Dict[str, Any] = {"ids": ",".join(ids)}

        return self.request(route, params=payload)

    def is_saved_track(self, ids: List[str]) -> Awaitable:
        """Check if one or more tracks is already saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        ids : List[:class:`str`]
            A list of the Spotify IDs.
        """
        route = self.route("GET", "/me/tracks/contains")
        payload: Dict[str, Any] = {"ids": ",".join(ids)}

        return self.request(route, params=payload)

    def saved_albums(
        self,
        *,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        market: Optional[str] = None,
    ) -> Awaitable:
        """Get a list of the albums saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        limit : Optional[:class:`str`]
            The maximum number of objects to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[:class:`str`]
            The index of the first object to return. Default: 0 (i.e., the first object). Use with limit to get the next set of objects.
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string from_token. Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/me/albums")
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if market is not None:
            payload["market"] = market

        return self.request(route, params=payload)

    def saved_tracks(
        self,
        *,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        market: Optional[str] = None,
    ) -> Awaitable:
        """Get a list of the songs saved in the current Spotify user’s ‘Your Music’ library.

        Parameters
        ----------
        limit : Optional[:class:`str`]
            The maximum number of objects to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[:class:`str`]
            The index of the first object to return. Default: 0 (i.e., the first object). Use with limit to get the next set of objects.
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string from_token. Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/me/tracks")
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def delete_saved_albums(self, ids: List[str]) -> Awaitable:
        """Remove one or more albums from the current user’s ‘Your Music’ library.

        Parameters
        ----------
        ids : List[:class:`str`]
            A list of the Spotify IDs.
        """
        route = self.route("DELETE", "/me/albums")
        return self.request(route, json=ids)

    def delete_saved_tracks(self, ids: List[str]) -> Awaitable:
        """Remove one or more tracks from the current user’s ‘Your Music’ library.

        Parameters
        ----------
        ids : List[:class:`str`]
            A list of the Spotify IDs.
        """
        route = self.route("DELETE", "/me/tracks")
        return self.request(route, json=ids)

    def save_tracks(self, ids: List[str]) -> Awaitable:
        """Save one or more tracks to the current user’s ‘Your Music’ library.

        Parameters
        ----------
        ids : List[:class:`str`]
            A list of the Spotify IDs.
        """
        route = self.route("PUT", "/me/tracks")
        return self.request(route, json=ids)

    def save_albums(self, ids: List[str]) -> Awaitable:
        """Save one or more albums to the current user’s ‘Your Music’ library.

        Parameters
        ----------
        ids : List[:class:`str`]
            A list of the Spotify IDs.
        """
        route = self.route("PUT", "/me/albums")
        return self.request(route, json=ids)

    def top_artists_or_tracks(
        self,
        type_: str,
        *,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        time_range: Optional[str] = None,
    ) -> Awaitable:
        """Get the current user’s top artists or tracks based on calculated affinity.

        Affinity is a measure of the expected preference a user has for a particular track or artist.
        It is based on user behavior, including play history, but does not include actions made while in incognito mode.
        Light or infrequent users of Spotify may not have sufficient play history to generate a full affinity data set.

        As a user’s behavior is likely to shift over time, this preference data is available over three time spans.

        For each time range, the top 50 tracks and artists are available for each user.
        In the future, it is likely that this restriction will be relaxed. This data is typically updated once each day for each user.

        Parameters
        ----------
        type_ : :class;`str`
            The type of entity to return. Valid values: "artists" or "tracks".
        limit : Optional[:class:`int`]
            The number of entities to return. Default: 20. Minimum: 1. Maximum: 50. For example: limit=2
        offset : Optional[:class:`int`]
            The index of the first entity to return. Default: 0 (i.e., the first track). Use with limit to get the next set of entities.
        time_range : Optional[:class:`str`]
            Over what time frame the affinities are computed.
            Valid values:
            - "long_term" (calculated from several years of data and including all new data as it becomes available)
            - "medium_term" (approximately last 6 months)
            - "short_term" (approximately last 4 weeks). Default: medium_term.
        """
        route = self.route("GET", "/me/top/{type_}", type_=type_)
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if time_range is not None:
            payload["time_range"] = time_range

        return self.request(route, params=payload)

    def available_devices(self) -> Awaitable:
        """Get information about a user’s available devices."""
        route = self.route("GET", "/me/player/devices")
        return self.request(route)

    def current_player(self, *, market: Optional[str] = None) -> Awaitable:
        """Get information about the user’s current playback state, including track, track progress, and active device.

        Parameters
        ----------
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string from_token. Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/me/player")
        payload: Dict[str, Any] = {}

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def playback_queue(self, *, uri: str, device_id: Optional[str] = None) -> Awaitable:
        """Add an item to the end of the user’s current playback queue.

        Parameters
        ----------
        uri : :class:`str`
            The uri of the item to add to the queue. Must be a track or an
            episode uri.
        device_id : :class:`str`
            The id of the device this command is targeting. If not supplied,
            the user’s currently active device is the target.
        """
        route = self.route("POST", "/me/player/queue")
        params = {"uri": uri}

        if device_id is not None:
            params["device_id"] = device_id

        return self.request(route, params=params)

    def recently_played(
        self,
        *,
        limit: Optional[int] = 20,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> Awaitable:
        """Get tracks from the current user’s recently played tracks.

        Returns the most recent 50 tracks played by a user.
        Note that a track currently playing will not be visible in play history until it has completed.
        A track must be played for more than 30 seconds to be included in play history.

        Any tracks listened to while the user had “Private Session” enabled in their client will not be returned in the list of recently played tracks.

        The endpoint uses a bidirectional cursor for paging.
        Follow the next field with the before parameter to move back in time, or use the after parameter to move forward in time.
        If you supply no before or after parameter, the endpoint will return the most recently played songs, and the next link will page back in time.

        Parameters
        ----------
        limit : Optional[:class:`int`]
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        after : Optional[:class:`str`]
            A Unix timestamp in milliseconds. Returns all items after (but not including) this cursor position. If after is specified, before must not be specified.
        before : Optional[:class:`str`]
            A Unix timestamp in milliseconds. Returns all items before (but not including) this cursor position. If before is specified, after must not be specified.
        """
        route = self.route("GET", "/me/player/recently-played")
        payload: Dict[str, Any] = {"limit": limit}

        if before:
            payload["before"] = before
        elif after:
            payload["after"] = after

        return self.request(route, params=payload)

    def currently_playing(self, *, market: Optional[str] = None) -> Awaitable:
        """Get the object currently being played on the user’s Spotify account.

        Parameters
        ----------
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string from_token. Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/me/player/currently-playing")
        payload: Dict[str, Any] = {}

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def pause_playback(self, *, device_id: Optional[str] = None) -> Awaitable:
        """Pause playback on the user’s account.

        Parameters
        ----------
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("PUT", "/me/player/pause")
        payload: Dict[str, Any] = {}

        if device_id:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def seek_playback(
        self, position_ms: int, *, device_id: Optional[str] = None
    ) -> Awaitable:
        """Seeks to the given position in the user’s currently playing track.

        Parameters
        ----------
        position_ms : :class:`int`
            The position in milliseconds to seek to. Must be a positive number. Passing in a position that is greater than the length of the track will cause the player to start playing the next song.
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("PUT", "/me/player/seek")
        payload: Dict[str, Any] = {"position_ms": position_ms}

        if device_id:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def repeat_playback(
        self, state: str, *, device_id: Optional[str] = None
    ) -> Awaitable:
        """Set the repeat mode for the user’s playback. Options are repeat-track, repeat-context, and off.

        Parameters
        ----------
        state : :class:`str`
            "track", "context" or "off".
             - track will repeat the current track.
             - context will repeat the current context.
             - off will turn repeat off.
        device_id : Optional[str]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("PUT", "/me/player/repeat")
        payload: Dict[str, Any] = {"state": state}

        if device_id:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def set_playback_volume(
        self, volume: int, *, device_id: Optional[str] = None
    ) -> Awaitable:
        """Set the volume for the user’s current playback device.

        Parameters
        ----------
        volume : :class:`int`
            The volume to set. Must be a value from 0 to 100 inclusive.
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("PUT", "/me/player/volume")
        payload: Dict[str, Any] = {"volume_percent": volume}

        if device_id:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def skip_next(self, *, device_id: Optional[str] = None) -> Awaitable:
        """Skips to next track in the user’s queue.

        Parameters
        ----------
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("POST", "/me/player/next")
        payload: Dict[str, Any] = {}

        if device_id:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def skip_previous(self, *, device_id: Optional[str] = None) -> Awaitable:
        """Skips to previous track in the user’s queue.

        Parameters
        ----------
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("POST", "/me/player/previous")
        payload: Dict[str, Any] = {}

        if device_id:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def play_playback(
        self,
        context_uri: Union[str, Sequence[str]],
        *,
        offset: Optional[Union[str, int]] = None,
        device_id: Optional[str] = None,
        position_ms: Optional[int] = 0,
    ) -> Awaitable:
        """Start a new context or resume current playback on the user’s active device.

        .. note::

            In order to resume playback set the context_uri to None.

        Parameters
        ----------
        context_uri : Union[str, Sequence[:class:`str`]]
            The context to play, if it is a string
            then it must be a uri of a album, artist
            or playlist.

            Otherwise a sequece of strings can be passed
            in and they must all be track URIs
        offset : Optional[Union[:class:`str`, :class:`int`]]
            The offset of which to start from,
            must either be an integer or a track URI.
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        position_ms : Optional[:class:`int`]
            indicates from what position to start playback. Must be a positive number.
            Passing in a position that is greater than the length of the track will cause the player to start playing the next song.
        """
        route = self.route("PUT", "/me/player/play")
        payload: Dict[str, Any] = {"position_ms": position_ms}
        params: Dict[str, Any] = {}
        can_set_offset: bool = False

        if isinstance(context_uri, str):
            payload["context_uri"] = context_uri
            can_set_offset = "playlist" in context_uri or "album" in context_uri

        elif hasattr(context_uri, "__iter__"):
            payload["uris"] = list(context_uri)
            can_set_offset = True

        elif context_uri is None:
            pass  # Do nothing, context_uri == None is allowed and intended for resume's

        else:
            raise TypeError(
                f"`context_uri` must be a string or an iterable object, got {type(context_uri)}"
            )

        if offset is not None:
            if can_set_offset:
                _offset: Dict[str, Union[int, str]]

                if isinstance(offset, str):
                    _offset = {"uri": offset}

                elif isinstance(offset, int):
                    _offset = {"position": offset}

                else:
                    raise TypeError(
                        f"`offset` should be either a string or an integer, got {type(offset)}"
                    )

                payload["offset"] = _offset
            else:
                raise ValueError(
                    "not able to set `offset` as either `context_uri` was not a list or it was a playlist or album uri."
                )

        if device_id is not None:
            params["device_id"] = device_id

        return self.request(route, params=params, json=payload)

    def shuffle_playback(
        self, state: bool, *, device_id: Optional[str] = None
    ) -> Awaitable:
        """Toggle shuffle on or off for user’s playback.

        Parameters
        ----------
        state : :class:`bool`
            True : Shuffle user’s playback
            False : Do not shuffle user’s playback.
        device_id : Optional[:class:`str`]
            The id of the device this command is targeting. If not supplied, the user’s currently active device is the target.
        """
        route = self.route("PUT", "/me/player/shuffle")
        payload: Dict[str, Any] = {"state": f"{bool(state)}".lower()}
        if device_id is not None:
            payload["device_id"] = device_id

        return self.request(route, params=payload)

    def transfer_player(
        self, device_id: str, *, play: Optional[bool] = False
    ) -> Awaitable:
        """Transfer playback to a new device and determine if it should start playing.

        .. note:

            Note that a value of false for the play parameter when also transferring to another device_id will not pause playback.
            To ensure that playback is paused on the new device you should send a pause command to the currently active device before transferring to the new device_id.

        Parameters
        ----------
        device_id : :class:`str`
            A Spotify Device ID
        play : Optional[:class:`bool`]
            True: ensure playback happens on new device.
            False or not provided: keep the current playback state.
        """
        route = self.route("PUT", "/me/player")
        payload: Dict[str, Any] = {"device_ids": [device_id], "play": play}

        return self.request(route, json=payload)

    def add_playlist_tracks(
        self,
        playlist_id: str,
        tracks: Sequence[Union[str]],
        position: Optional[int] = None,
    ) -> Awaitable:
        """Add one or more tracks to a user’s playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        tracks : Sequence[Union[:class:`str`]]
            A sequence of track URIs.
        position : Optional[:class:`int`]
            The position to insert the tracks, a zero-based index.
        """
        route = self.route(
            "POST", "/playlists/{playlist_id}/tracks", playlist_id=playlist_id
        )

        payload: Dict[str, Any] = {"uris": [track for track in tracks]}

        if position is not None:
            payload["position"] = position

        return self.request(route, json=payload)

    def change_playlist_details(
        self,
        playlist_id: str,
        *,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        collaborative: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> Awaitable:
        """Change a playlist’s name and public/private state. (The user must, of course, own the playlist.)

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        name : :class:`str`
            The name for the new playlist
        public : Optional[:class:`bool`]
            Defaults to true . If true the playlist will be public, if false it will be private
        collaborative : Optional[:class:`bool`]
            Defaults to false . If true the playlist will be collaborative.

            .. note::
                to create a collaborative playlist you must also set public to false
        description : Optional[:class:`str`]
            The value for playlist description as displayed in Spotify Clients and in the Web API.
        """
        route = self.route("PUT", "/playlists/{playlist_id}", playlist_id=playlist_id)

        payload: Dict[str, Any] = filter_items(
            {
                "name": name,
                "public": public,
                "collaborative": collaborative,
                "description": description,
            }
        )

        return self.request(route, json=payload)

    def create_playlist(
        self,
        user_id: str,
        *,
        name: str,
        public: Optional[bool] = True,
        collaborative: Optional[bool] = False,
        description: Optional[str] = "",
    ) -> Awaitable:
        """Create a playlist for a Spotify user. (The playlist will be empty until you add tracks.)

        Parameters
        ----------
        user_id : :class:`str`
            The user’s Spotify user ID.
        name : :class:`str`
            The name for the new playlist
        public : Optional[:class:`bool`]
            Defaults to true . If true the playlist will be public, if false it will be private
        collaborative : Optional[:class:`bool`]
            Defaults to false . If true the playlist will be collaborative.

            .. note::
                to create a collaborative playlist you must also set public to false
        description : Optional[:class:`str`]
            The value for playlist description as displayed in Spotify Clients and in the Web API.
        """
        route = self.route("POST", "/users/{user_id}/playlists", user_id=user_id)

        payload: Dict[str, Any] = {
            "name": name,
            "public": public,
            "collaborative": collaborative,
            "description": description,
        }

        return self.request(route, json=payload)

    def follow_playlist(
        self, playlist_id: str, *, public: Optional[bool] = True
    ) -> Awaitable:
        """Add the current user as a follower of a playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID of the playlist. Any playlist can be followed, regardless of its public/private status, as long as you know its playlist ID.
        public : Optional[:class:`bool`]
            Defaults to true. If true the playlist will be included in user’s public playlists, if false it will remain private.
        """
        route = self.route(
            "PUT", "/playlists/{playlist_id}/followers", playlist_id=playlist_id
        )

        payload: Dict[str, Any] = {"public": public}

        return self.request(route, json=payload)

    def current_playlists(
        self, *, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> Awaitable:
        """Get a list of the playlists owned or followed by the current Spotify user.

        Parameters
        ----------
        limit : Optional[:class:`str`]
            The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[:class:`str`]
            he index of the first playlist to return. Default: 0 (the first object). Maximum offset: 100.000.
        """
        route = self.route("GET", "/me/playlists")
        return self.request(route, params={"limit": limit, "offset": offset})

    def get_playlists(
        self, user_id: str, *, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> Awaitable:
        """Get a list of the playlists owned or followed by a Spotify user.

        Parameters
        ----------
        user_id : :class:`str`
            The user’s Spotify user ID.
        limit : Optional[:class:`str`]
            The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[:class:`str`]
            he index of the first playlist to return. Default: 0 (the first object). Maximum offset: 100.000.
        """
        route = self.route("GET", "/users/{user_id}/playlists", user_id=user_id)
        return self.request(route, params={"limit": limit, "offset": offset})

    def get_playlist_cover_image(self, playlist_id: str) -> Awaitable:
        """Get the current image associated with a specific playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        """
        route = self.route(
            "GET", "/playlists/{playlist_id}/images", playlist_id=playlist_id
        )
        return self.request(route)

    def get_playlist(
        self,
        playlist_id: str,
        *,
        fields: Optional[str] = None,
        market: Optional[str] = None,
    ) -> Awaitable:
        """Get a playlist owned by a Spotify user.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        fields: Optional[:class:`str`]
            Filters for the query: a comma-separated list of the fields to return.
            If omitted, all fields are returned. For example, to get just the total number of tracks and the request limit: `fields=total,limit`

            A dot separator can be used to specify non-reoccurring fields, while parentheses can be used to specify reoccurring fields within objects.
            For example, to get just the added date and user ID of the adder: `fields=items(added_at,added_by.id)`

            Use multiple parentheses to drill down into nested objects, for example: `fields=items(track(name,href,album(name,href)))`

            Fields can be excluded by prefixing them with an exclamation mark, for example: `fields=items.track.album(!external_urls,images)`
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string "from_token".
            Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/playlists/{playlist_id}", playlist_id=playlist_id)
        payload: Dict[str, Any] = {}

        if fields:
            payload["fields"] = fields

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def get_playlist_tracks(
        self,
        playlist_id: str,
        *,
        fields: Optional[str] = None,
        market: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ) -> Awaitable:
        """Get full details of the tracks of a playlist owned by a Spotify user.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        fields: Optional[:class:`str`]
            Filters for the query: a comma-separated list of the fields to return.
            If omitted, all fields are returned. For example, to get just the total number of tracks and the request limit: `fields=total,limit`

            A dot separator can be used to specify non-reoccurring fields, while parentheses can be used to specify reoccurring fields within objects.
            For example, to get just the added date and user ID of the adder: `fields=items(added_at,added_by.id)`

            Use multiple parentheses to drill down into nested objects, for example: `fields=items(track(name,href,album(name,href)))`

            Fields can be excluded by prefixing them with an exclamation mark, for example: `fields=items.track.album(!external_urls,images)`
        limit : Optional[:class:`str`]
            The maximum number of tracks to return. Default: 100. Minimum: 1. Maximum: 100.
        offset : Optional[:class:`str`]
            The index of the first track to return. Default: 0 (the first object).
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string "from_token".
            Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route(
            "GET", "/playlists/{playlist_id}/tracks", playlist_id=playlist_id
        )
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}

        if fields:
            payload["fields"] = fields

        if market:
            payload["market"] = market

        return self.request(route, params=payload)

    def remove_playlist_tracks(
        self,
        playlist_id: str,
        tracks: Sequence[Union[str, Dict[str, Any]]],
        *,
        snapshot_id: str = None,
    ) -> Awaitable:
        """Remove one or more tracks from a user’s playlist.

        Parameters
        ----------
        playlist_id : str
            The id of the playlist to target
        tracks : Sequence[Union[str, Dict[str, Union[str, int]]]]
            Either a sequence of track URIs to remove a specific occurence
            of a track or for targeted removal pass in a dict that looks like
            `{'uri': URI, 'position': POSITIONS}` where `URI` is  track URI and
            `POSITIONS` is an list of integers
        snapshot_id : Optional[str]
            The snapshot to target.
        """
        route = self.route(
            "DELETE ", "/playlists/{playlist_id}/tracks", playlist_id=playlist_id
        )
        payload: Dict[str, Any] = {
            "tracks": [
                ({"uri": track} if isinstance(track, str) else track)
                for track in tracks
            ]
        }

        if snapshot_id:
            payload["snapshot_id"] = snapshot_id

        return self.request(route, json=payload)

    def reorder_playlists_tracks(
        self,
        playlist_id: str,
        range_start: int,
        range_length: int,
        insert_before: int,
        *,
        snapshot_id: Optional[str] = None,
    ) -> Awaitable:
        """Reorder a track or a group of tracks in a playlist.

        Visualization of how reordering tracks works

        .. image:: /images/visualization-reordering-tracks.png

        .. note::
            When reordering tracks, the timestamp indicating when they were added and the user who added them will be kept untouched.
            In addition, the users following the playlists won’t be notified about changes in the playlists when the tracks are reordered.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        range_start : :class:`int`
            The position of the first track to be reordered.
        range_length : :class:`int`
            The amount of tracks to be reordered. Defaults to 1 if not set.

            The range of tracks to be reordered begins from the range_start position, and includes the range_length subsequent tracks.
        insert_before : :class:`int`
            The position where the tracks should be inserted.

            To reorder the tracks to the end of the playlist, simply set insert_before to the position after the last track.
        snapshot_id : Optional[:class:`str`]
            The playlist’s snapshot ID against which you want to make the changes.
        """
        route = self.route(
            "PUT", "/playlists/{playlist_id}/tracks", playlist_id=playlist_id
        )
        payload: Dict[str, Any] = {
            "range_start": range_start,
            "range_length": range_length,
            "insert_before": insert_before,
        }

        if snapshot_id:
            payload["snapshot_id"] = snapshot_id

        return self.request(route, json=payload)

    def replace_playlist_tracks(
        self, playlist_id: str, tracks: Sequence[str]
    ) -> Awaitable:
        """Replace all the tracks in a playlist, overwriting its existing tracks.

        .. note::

            This powerful request can be useful for replacing tracks, re-ordering existing tracks, or clearing the playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        tracks : Sequence[:class:`str`]
            A list of tracks to replace with.
        """
        route = self.route(
            "PUT", "/playlists/{playlist_id}/tracks", playlist_id=playlist_id
        )
        payload: Dict[str, Any] = {"uris": tuple(tracks)}

        return self.request(route, json=payload)

    def upload_playlist_cover_image(
        self, playlist_id: str, file: BinaryIO
    ) -> Awaitable:
        """Replace the image used to represent a specific playlist.

        Parameters
        ----------
        playlist_id : :class:`str`
            The Spotify ID for the playlist.
        file : File-like object
            An file-like object that supports reading
            the contents that are being read should be :class:`bytes`
        """
        route = self.route(
            "PUT", "/playlists/{playlist_id}/images", playlist_id=playlist_id
        )
        return self.request(
            route, data=b64encode(file.read()), content_type="image/jpeg"
        )

    def track_audio_analysis(self, track_id: str) -> Awaitable:
        """Get a detailed audio analysis for a single track identified by its unique Spotify ID.

        The Audio Analysis endpoint provides low-level audio analysis for all of the tracks in the Spotify catalog.
        The Audio Analysis describes the track’s structure and musical content, including rhythm, pitch, and timbre.
        All information is precise to the audio sample.

        Many elements of analysis include confidence values, a floating-point number ranging from 0.0 to 1.0.
        Confidence indicates the reliability of its corresponding attribute.
        Elements carrying a small confidence value should be considered speculative.
        There may not be sufficient data in the audio to compute the attribute with high certainty.

        Parameters
        ----------
        track_id : :class:`str`
            The Spotify ID for the track.
        """
        route = self.route("GET", "/audio-analysis/{id}", id=track_id)
        return self.request(route)

    def track_audio_features(self, track_id: str) -> Awaitable:
        """Get audio feature information for a single track identified by its unique Spotify ID.

        Parameters
        ----------
        track_id : :class:`str`
            The Spotify ID for the track.
        """
        route = self.route("GET", "/audio-features/{id}", id=track_id)
        return self.request(route)

    def audio_features(self, track_ids: List[str]) -> Awaitable:
        """Get audio features for multiple tracks based on their Spotify IDs.

        Parameters
        ----------
        track_ids : List[:class:`str`]
            A comma-separated list of the Spotify IDs for the tracks. Maximum: 100 IDs.
        """
        route = self.route("GET", "/audio-features")
        return self.request(route, params={"ids": track_ids})

    def track(self, track_id: str, market: Optional[str] = None) -> Awaitable:
        """Get Spotify catalog information for a single track identified by its unique Spotify ID.

        Parameters
        ----------
        track_id : :class:`str`
            The Spotify ID for the track.
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string "from_token".
            Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/tracks/{id}", id=track_id)
        payload: Dict[str, Any] = {}

        if market is not None:
            payload["market"] = market

        return self.request(route, params=payload)

    def tracks(self, track_ids: List[str], market: Optional[str] = None) -> Awaitable:
        """Get Spotify catalog information for multiple tracks based on their Spotify IDs.

        Parameters
        ----------
        track_ids : List[:class:`str`]
            A comma-separated list of the Spotify IDs for the tracks. Maximum: 50 IDs.
        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string "from_token".
            Provide this parameter if you want to apply Track Relinking.
        """
        route = self.route("GET", "/tracks")
        payload: Dict[str, Any] = {"ids": track_ids}

        if market is not None:
            payload["market"] = market

        return self.request(route, params=payload)

    def current_user(self) -> Awaitable:
        """Get detailed profile information about the current user (including the current user’s username)."""
        route = self.route("GET", "/me")
        return self.request(route)

    def user(self, user_id: str) -> Awaitable:
        """Get public profile information about a Spotify user.

        Parameters
        ---------
        user_id : class:`str`
            The user’s Spotify user ID.
        """
        route = self.route("GET", "/users/{user_id}", user_id=user_id)
        return self.request(route)

    def search(  # pylint: disable=invalid-name
        self,
        q: str,
        query_type: str = "track,playlist,artist,album",
        market: str = "US",
        limit: int = 20,
        offset: int = 0,
        include_external: Optional[str] = None,
    ) -> Awaitable:
        """Get Spotify Catalog information about artists, albums, tracks or playlists that match a keyword string.

        Parameters
        ----------
        q : :class:`str`
            Search query keywords and optional field filters and operators. e.g. `roadhouse blues.`

        query_type : Optional[:class:`str`]
            A comma-separated list of item types to search across. (default: "track,playlist,artist,album")
            Valid types are: album, artist, playlist, and track.
            Search results include hits from all the specified item types.

        market : Optional[:class:`str`]
            An ISO 3166-1 alpha-2 country code or the string "from_token". (default: "US")
            If a country code is specified, only artists, albums, and tracks with content that is playable in that market is returned.

            .. note::
                - Playlist results are not affected by the market parameter.
                - If market is set to "from_token", and a valid access token is specified in the request header, only
                    content playable in the country associated with the user account, is returned.
                - Users can view the country that is associated with their account in the account settings. A user must
                    grant access to the user-read-private scope prior to when the access token is issued.

        limit : Optional[:class:`int`]
            Maximum number of results to return. (Default: 20, Minimum: 1, Maximum: 50)

            .. note::
                The limit is applied within each type, not on the total response.
                For example, if the limit value is 3 and the type is artist,album, the response contains 3 artists and 3 albums.

        offset : Optional[:class:`int`]
            The index of the first result to return.
            Default: 0 (the first result).
            Maximum offset (including limit): 10,000.
            Use with limit to get the next page of search results.

        include_external : Optional[:class:`str`]
            Possible values: `audio`
            If `include_external=audio` is specified the response will include any relevant audio content that is hosted externally.
            By default external content is filtered out from responses.

        """
        route = self.route("GET", "/search")
        payload: Dict[str, Any] = {
            "q": quote(q),
            "type": query_type,
            "limit": limit,
            "offset": offset,
        }

        if market:
            payload["market"] = market

        if include_external is not None:
            payload["include_external"] = include_external

        return self.request(route, params=payload)


REFRESH_TOKEN_URL = "https://accounts.spotify.com/api/token?grant_type=refresh_token&refresh_token={refresh_token}"


class HTTPUserClient(HTTPClient):
    """HTTPClient for access to user endpoints."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token: str = None,
        refresh_token: str = None,
        loop=None,
    ):
        assert token or refresh_token
        super().__init__(client_id, client_secret, loop=loop)
        if token:
            self.bearer_info = {"access_token": token}
        self.refresh_token = refresh_token

    async def get_bearer_info(self, *_, **__):
        if not self.refresh_token:
            # Should only happen if User.from_token didn't receive refresh_token
            raise SpotifyException(
                "Access token expired and no refresh token was provided"
            )

        headers = {
            "Authorization": f"Basic {b64encode(':'.join((self.client_id, self.client_secret)).encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        route = ("POST", REFRESH_TOKEN_URL.format(refresh_token=self.refresh_token))
        return await self.request(route, headers=headers)
