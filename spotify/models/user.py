"""Source implementation for a spotify User"""

import asyncio
import functools
import json
import time
from base64 import b64encode
from pathlib import Path
from typing import (
    Optional,
    Dict,
    List,
    Tuple,
    Type,
    TypeVar,
    Union,
    Coroutine,
    TYPE_CHECKING,
    Any)

from ..utils import to_id
from ..http import HTTPUserClient
from . import URIBase, Image, Device, Context, Player, Playlist, Track, Artist, Library

if TYPE_CHECKING:
    import spotify

T = TypeVar("T", Artist, Track)

REFRESH_TOKEN_URL = "https://accounts.spotify.com/api/token?grant_type=refresh_token&refresh_token={refresh_token}"


class TokenInfo:
    def __init__(
            self,
            access_token: Optional[str] = None,
            expires_in: Optional[int] = None,
            token_type: Optional[str] = None,
            refresh_token: Optional[str] = None,
            scope: Optional[str] = None,
            **kwargs
    ):
        self.access_token = access_token
        self.expires_in = expires_in
        self.token_type = token_type
        self.refresh_token = refresh_token
        self.scope = scope
        self.expires_at = time.time() + self.expires_in if self.expires_in else None

    def is_token_valid(self) -> bool:
        if self.access_token and self.expires_at and self.expires_at > time.time():
            return True
        return False

    def serialize(self):
        return {
            'access_token': self.access_token,
            'expires_in': self.expires_in,
            'expires_at': self.expires_at,
            'scope': self.scope,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type
        }

    @classmethod
    def from_file(cls, file_path: Path):
        data: Dict[str, Any] = {}
        try:
            data = json.loads(file_path.read_text())
        except (IOError, json.JSONDecodeError):
            pass
        return cls(**data)


async def _refresh_token(client: "spotify.Client", refresh_token: str) -> TokenInfo:
    client_id = client.http.client_id
    client_secret = client.http.client_secret

    headers = {
        "Authorization": f"Basic {b64encode(':'.join((client_id, client_secret)).encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    route = ("POST", REFRESH_TOKEN_URL.format(refresh_token=refresh_token))
    data = await client.http.request(route, headers=headers)

    return TokenInfo(**data)


def ensure_http(func):
    func.__ensure_http__ = True
    return func


class User(URIBase):  # pylint: disable=too-many-instance-attributes
    """A Spotify User.

    Attributes
    ----------
    id : :class:`str`
        The Spotify user ID for the user.
    uri : :class:`str`
        The Spotify URI for the user.
    url : :class:`str`
        The open.spotify URL.
    href : :class:`str`
        A link to the Web API endpoint for this user.
    display_name : :class:`str`
        The name displayed on the user’s profile.
        `None` if not available.
    followers : :class:`int`
        The total number of followers.
    images : List[:class:`Image`]
        The user’s profile image.
    email : :class:`str`
        The user’s email address, as entered by the user when creating their account.
    country : :class:`str`
        The country of the user, as set in the user’s account profile. An ISO 3166-1 alpha-2 country code.
    birthdate : :class:`str`
        The user’s date-of-birth.
    product : :class:`str`
        The user’s Spotify subscription level: “premium”, “free”, etc.
        (The subscription level “open” can be considered the same as “free”.)
    """

    _refresh_task: Optional[asyncio.Task]

    def __init__(
            self,
            client: "spotify.Client",
            data: dict,
            token_info: Optional[TokenInfo] = None,
            refresh: bool = False,
            **kwargs
    ):
        self._refresh_task = None
        self.__client = self.client = client

        try:
            self.http = kwargs.pop("http")
        except KeyError:
            pass  # TODO: Failing silently here, we should take some action.
        else:
            self.library = Library(client, self)

        self.token_info: TokenInfo = token_info or TokenInfo()

        self._cache_path: Optional[Path] = kwargs.pop("cache_path", None)
        if self._cache_path and not self._cache_path.exists():  # make sure the file and folders exist
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.touch(exist_ok=True)
        self._save_to_cache(self.token_info)

        if refresh and self.token_info.refresh_token and self.token_info.expires_in:
            coroutine: Coroutine = self._refreshing_token(
                self.token_info.expires_in, self.token_info.refresh_token
            )  # pylint: disable=protected-access

            self._refresh_task = self.client.loop.create_task(
                coroutine
            )  #

        # Public user object attributes
        self.id = data.pop("id")  # pylint: disable=invalid-name
        self.uri = data.pop("uri")
        self.url = data.pop("external_urls").get("spotify", None)
        self.display_name = data.pop("display_name", None)
        self.href = data.pop("href")
        self.followers = data.pop("followers", {}).get("total", None)
        self.images = list(Image(**image) for image in data.pop("images", []))

        # Private user object attributes
        self.email = data.pop("email", None)
        self.country = data.pop("country", None)
        self.birthdate = data.pop("birthdate", None)
        self.product = data.pop("product", None)

    def __repr__(self):
        return f"<spotify.User: {(self.display_name or self.id)!r}>"

    def __getattr__(self, attr):
        value = object.__getattribute__(self, attr)

        if hasattr(value, "__ensure_http__") and not hasattr(self, "http"):
            @functools.wraps(value)
            def _raise(*args, **kwargs):
                raise AttributeError(
                    "User has not HTTP presence to perform API requests."
                )

            return _raise
        return value

    async def _get_top(self, klass: Type[T], kwargs: dict) -> List[T]:
        target = {Artist: "artists", Track: "tracks"}[klass]
        data = {
            key: value
            for key, value in kwargs.items()
            if key in ("limit", "offset", "time_range")
        }

        resp = await self.http.top_artists_or_tracks(target, **data)

        return [klass(self.__client, item) for item in resp["items"]]

    async def _refreshing_token(self, expires: int, token: str) -> None:
        while True:
            await asyncio.sleep(expires - 1)

            self.token_info = await _refresh_token(self.client, token)

            self._save_to_cache(self.token_info)

            expires = self.token_info.expires_in or expires
            self.http.token = self.token_info.access_token

    def _save_to_cache(self, token_info: TokenInfo) -> bool:
        if not self._cache_path or not self._cache_path.exists():
            return True

        try:
            self._cache_path.write_text(json.dumps(token_info.serialize()))
        except IOError:
            return False

        return True

    ### Alternate constructors

    @classmethod
    async def from_code(
        cls,
        client: "spotify.Client",
        code: str,
        *,
        redirect_uri: str,
        cache_path: Optional[Union[Path, str]] = None,
        refresh: bool = False,
    ):
        """Create a :class:`User` object from an authorization code.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        code : :class:`str`
            The authorization code to use to further authenticate the user.
        redirect_uri : :class:`str`
            The rediriect URI to use in tandem with the authorization code.
        cache_path: Optional[Union[:class:`Path`, :class:`str`]]
            Optional path to a cache file where tokens and refresh
            tokens will be saved.
        refresh : :class:`bool`
            Wether to keep the http session authorized.
        """
        route = ("POST", "https://accounts.spotify.com/api/token")
        payload = {
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code": code,
        }

        client_id = client.http.client_id
        client_secret = client.http.client_secret

        headers = {
            "Authorization": f"Basic {b64encode(':'.join((client_id, client_secret)).encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = await client.http.request(route, headers=headers, params=payload)

        token_info = TokenInfo(**data)

        return await cls.from_token_info(client, token_info, cache_path, refresh)

    @classmethod
    async def from_token(
        cls,
        client: "spotify.Client",
        token: str,
        *,
        cache_path: Optional[Union[Path, str]] = None,
        refresh: Optional[Tuple[int, str]] = None,
    ):
        """Create a :class:`User` object from an access token.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        token : :class:`str`
            The access token to use for http requests.
        cache_path: Optional[Union[:class:`Path`, :class:`str`]]
            Optional path to a cache file where tokens and refresh
            tokens will be saved.
        refresh : Optional[Tuple[:class:`int`, :class:`str`]]
            When provided the refresh argument must be a tuple
            of an integer representing the number of seconds until
            the access token expires and a string representing the
            refresh token to use to generate a new access token.
        """
        if refresh is not None:
            if not isinstance(refresh, tuple):
                raise ValueError(f"refresh must be a tuple of an int and str.")

            if not len(refresh) == 2:
                raise ValueError(f"refresh must have exactly two elements.")

        if refresh:
            token_info = TokenInfo(access_token=token, expires_in=refresh[0], refresh_token=refresh[1])
        else:
            token_info = TokenInfo(access_token=token)

        return await cls.from_token_info(client, token_info, cache_path, refresh=bool(refresh))

    @classmethod
    async def from_token_info(
            cls,
            client: "spotify.Client",
            token_info: TokenInfo,
            cache_path: Optional[Union[Path, str]] = None,
            refresh: bool = False
    ) -> "spotify.User":
        """Create a :class:`User` object from token information.
        Either from a provided access or refresh token.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        token_info : :class:`TokenInfo`
            The token information to authenticate the User object
            with. Contains an access_token with corresponding
            expires_at information in seconds, refresh_token
            or both.
        cache_path: Optional[Union[:class:`Path`, :class:`str`]]
            Optional path to a cache file where tokens and refresh
            tokens will be saved.
        refresh : Optional[Tuple[:class:`int`, :class:`str`]]
            When provided the refresh argument must be a tuple
            of an integer representing the number of seconds until
            the access token expires and a string representing the
            refresh token to use to generate a new access token.
        """
        if cache_path and isinstance(cache_path, str):
            cache_path = Path(cache_path)

        if not token_info.is_token_valid():
            # expired access token, need to use refresh token
            if not token_info.refresh_token:
                raise Exception("Invalid access token and no refresh token provided")

            headers = {
                "Authorization":
                    f"Basic {b64encode(':'.join((client.http.client_id, client.http.client_secret)).encode()).decode()}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            route = ("POST", REFRESH_TOKEN_URL.format(refresh_token=token_info.refresh_token))
            token_info = TokenInfo(**await client.http.request(route, headers=headers))

        http = HTTPUserClient(token_info.access_token)

        data = await http.current_user()

        return cls(
            client,
            data=data,
            http=http,
            token_info=token_info,
            refresh=refresh,
            cache_path=cache_path
        )

    @classmethod
    async def from_cache(
            cls,
            client: "spotify.Client",
            cache_path: Union[Path, str],
            refresh: bool = False
    ) -> "spotify.User":
        """Create a :class:`User` object from cached token information.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        cache_path: Optional[Union[:class:`Path`, :class:`str`]]
            Optional path to a cache file where tokens and refresh
            tokens will be saved.
        refresh : :class:`bool`
            Wether to keep the http session authorized.
        """
        if isinstance(cache_path, str):
            cache_path = Path(cache_path)

        if not cache_path.exists():
            raise FileNotFoundError("Cache file does not exist.")

        token_info = TokenInfo.from_file(cache_path)

        return await cls.from_token_info(client, token_info, cache_path, refresh=refresh)

    ### Attributes

    @property
    def refresh(self):
        """Optional[:class:`asyncio.Task`] - An asyncio task that is handling the session refresh or None if not refreshing."""
        return self._refresh_task

    ### Contextual methods

    @ensure_http
    async def currently_playing(self) -> Dict[str, Union[Track, Context, str]]:
        """Get the users currently playing track.

        Returns
        -------
        context, track : Dict[str, Union[Track, Context, str]]
            A tuple of the context and track.
        """
        data = await self.http.currently_playing()

        if "item" in data:
            context = data.pop("context", None)

            if context is not None:
                data["context"] = Context(context)
            else:
                data["context"] = None

            data["item"] = Track(self.__client, data.get("item", {}) or {})

        return data

    @ensure_http
    async def get_player(self) -> Player:
        """Get information about the users current playback.

        Returns
        -------
        player : :class:`Player`
            A player object representing the current playback.
        """
        player = Player(self.__client, self, await self.http.current_player())
        return player

    @ensure_http
    async def get_devices(self) -> List[Device]:
        """Get information about the users avaliable devices.

        Returns
        -------
        devices : List[:class:`Device`]
            The devices the user has available.
        """
        data = await self.http.available_devices()
        return [Device(item) for item in data["devices"]]

    @ensure_http
    async def recently_played(self) -> List[Dict[str, Union[Track, Context, str]]]:
        """Get tracks from the current users recently played tracks.

        Returns
        -------
        playlist_history : List[Dict[:class:`str`, Union[Track, Context, :class:`str`]]]
            A list of playlist history object.
            Each object is a dict with a timestamp, track and context field.
        """
        data = await self.http.recently_played()
        client = self.__client

        # List[T] where T: {'track': Track, 'content': Context: 'timestamp': ISO8601}
        return [
            {
                "played_at": track.get("played_at"),
                "context": Context(track.get("context", {}) or {}),
                "track": Track(client, track.get("track", {}) or {}),
            }
            for track in data["items"]
        ]

    ### Playlist track methods

    @ensure_http
    async def add_tracks(self, playlist: Union[str, Playlist], *tracks) -> str:
        """Add one or more tracks to a user’s playlist.

        Parameters
        ----------
        playlist : Union[:class:`str`, Playlist]
            The playlist to modify
        tracks : Sequence[Union[:class:`str`, Track]]
            Tracks to add to the playlist

        Returns
        -------
        snapshot_id : :class:`str`
            The snapshot id of the playlist.
        """
        data = await self.http.add_playlist_tracks(
            to_id(str(playlist)), tracks=(str(track) for track in tracks)
        )
        return data["snapshot_id"]

    @ensure_http
    async def replace_tracks(self, playlist, *tracks) -> None:
        """Replace all the tracks in a playlist, overwriting its existing tracks.

        This powerful request can be useful for replacing tracks, re-ordering existing tracks, or clearing the playlist.

        Parameters
        ----------
        playlist : Union[:class:`str`, PLaylist]
            The playlist to modify
        tracks : Sequence[Union[:class:`str`, Track]]
            Tracks to place in the playlist
        """
        await self.http.replace_playlist_tracks(
            to_id(str(playlist)), tracks=",".join(str(track) for track in tracks)
        )

    @ensure_http
    async def remove_tracks(self, playlist, *tracks):
        """Remove one or more tracks from a user’s playlist.

        Parameters
        ----------
        playlist : Union[:class:`str`, Playlist]
            The playlist to modify
        tracks : Sequence[Union[:class:`str`, Track]]
            Tracks to remove from the playlist

        Returns
        -------
        snapshot_id : :class:`str`
            The snapshot id of the playlist.
        """
        data = await self.http.remove_playlist_tracks(
            to_id(str(playlist)), tracks=(str(track) for track in tracks)
        )
        return data["snapshot_id"]

    @ensure_http
    async def reorder_tracks(
        self, playlist, start, insert_before, length=1, *, snapshot_id=None
    ):
        """Reorder a track or a group of tracks in a playlist.

        Parameters
        ----------
        playlist : Union[:class:`str`, Playlist]
            The playlist to modify
        start : int
            The position of the first track to be reordered.
        insert_before : int
            The position where the tracks should be inserted.
        length : Optional[int]
            The amount of tracks to be reordered. Defaults to 1 if not set.
        snapshot_id : :class:`str`
            The playlist’s snapshot ID against which you want to make the changes.

        Returns
        -------
        snapshot_id : :class:`str`
            The snapshot id of the playlist.
        """
        data = await self.http.reorder_playlists_tracks(
            to_id(str(playlist)), start, length, insert_before, snapshot_id=snapshot_id
        )
        return data["snapshot_id"]

    ### Playlist methods

    @ensure_http
    async def edit_playlist(
        self, playlist, *, name=None, public=None, collaborative=None, description=None
    ):
        """Change a playlist’s name and public/private, collaborative state and description.

        Parameters
        ----------
        playlist : Union[:class:`str`, Playlist]
            The playlist to modify
        name : Optional[:class:`str`]
            The new name of the playlist.
        public : Optional[bool]
            The public/private status of the playlist.
            `True` for public, `False` for private.
        collaborative : Optional[bool]
            If `True`, the playlist will become collaborative and other users will be able to modify the playlist.
        description : Optional[:class:`str`]
            The new playlist description
        """
        data = {}

        if name:
            data["name"] = name

        if public:
            data["public"] = public

        if collaborative:
            data["collaborative"] = collaborative

        if description:
            data["description"] = description

        await self.http.change_playlist_details(self.id, to_id(str(playlist)), **data)

    @ensure_http
    async def create_playlist(
        self, name, *, public=True, collaborative=False, description=None
    ):
        """Create a playlist for a Spotify user.

        Parameters
        ----------
        name : :class:`str`
            The name of the playlist.
        public : Optional[bool]
            The public/private status of the playlist.
            `True` for public, `False` for private.
        collaborative : Optional[bool]
            If `True`, the playlist will become collaborative and other users will be able to modify the playlist.
        description : Optional[:class:`str`]
            The playlist description

        Returns
        -------
        playlist : :class:`Playlist`
            The playlist that was created.
        """
        data = {"name": name, "public": public, "collaborative": collaborative}

        if description:
            data["description"] = description

        playlist_data = await self.http.create_playlist(self.id, **data)
        return Playlist(self.__client, playlist_data, http=self.http)

    @ensure_http
    async def follow_playlist(
        self, playlist: Union[str, Playlist], *, public: bool = True
    ) -> None:
        """follow a playlist

        Parameters
        ----------
        playlist : Union[:class:`str`, Playlist]
            The playlist to modify
        public : Optional[bool]
            The public/private status of the playlist.
            `True` for public, `False` for private.
        """
        await self.http.follow_playlist(to_id(str(playlist)), public=public)

    @ensure_http
    async def get_playlists(
        self, *, limit: int = 20, offset: int = 0
    ) -> List[Playlist]:
        """get the users playlists from spotify.

        Parameters
        ----------
         limit : Optional[int]
             The limit on how many playlists to retrieve for this user (default is 20).
         offset : Optional[int]
             The offset from where the api should start from in the playlists.

        Returns
        -------
        playlists : List[Playlist]
            A list of the users playlists.
        """
        data = await self.http.get_playlists(self.id, limit=limit, offset=offset)

        return [
            Playlist(self.__client, playlist_data, http=self.http)
            for playlist_data in data["items"]
        ]

    @ensure_http
    async def get_all_playlists(self) -> List[Playlist]:
        """Get all of the users playlists from spotify.

        Returns
        -------
        playlists : List[:class:`Playlist`]
            A list of the users playlists.
        """
        playlists: List[Playlist] = []
        total = None
        offset = 0

        while True:
            data = await self.http.get_playlists(self.id, limit=50, offset=offset)

            if total is None:
                total = data["total"]

            offset += 50
            playlists += [
                Playlist(self.__client, playlist_data, http=self.http)
                for playlist_data in data["items"]
            ]

            if len(playlists) >= total:
                break

        return playlists

    @ensure_http
    async def top_artists(self, **data) -> List[Artist]:
        """Get the current user’s top artists based on calculated affinity.

        Parameters
        ----------
        limit : Optional[int]
            The number of entities to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first entity to return. Default: 0
        time_range : Optional[:class:`str`]
            Over what time frame the affinities are computed. (long_term, short_term, medium_term)

        Returns
        -------
        tracks : List[Artist]
            The top artists for the user.
        """
        return await self._get_top(Artist, data)

    @ensure_http
    async def top_tracks(self, **data) -> List[Track]:
        """Get the current user’s top tracks based on calculated affinity.

        Parameters
        ----------
        limit : Optional[int]
            The number of entities to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : Optional[int]
            The index of the first entity to return. Default: 0
        time_range : Optional[:class:`str`]
            Over what time frame the affinities are computed. (long_term, short_term, medium_term)

        Returns
        -------
        tracks : List[Track]
            The top tracks for the user.
        """
        return await self._get_top(Track, data)
