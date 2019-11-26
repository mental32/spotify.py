"""Source implementation for a spotify User"""

import asyncio
import functools
from functools import partial
from base64 import b64encode
from typing import (
    Optional,
    Dict,
    Union,
    List,
    Tuple,
    Type,
    TypeVar,
    Coroutine,
    TYPE_CHECKING,
)

from ..utils import to_id
from ..http import HTTPUserClient
from . import (
    AsyncIterable,
    URIBase,
    Image,
    Device,
    Context,
    Player,
    Playlist,
    Track,
    Artist,
    Library,
)

if TYPE_CHECKING:
    import spotify

T = TypeVar("T", Artist, Track)  # pylint: disable=invalid-name


def ensure_http(func):
    func.__ensure_http__ = True
    return func


class User(URIBase, AsyncIterable):  # pylint: disable=too-many-instance-attributes
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

    def __init__(self, client: "spotify.Client", data: dict, **kwargs):
        self.__client = self.client = client

        if "http" not in kwargs:
            self.library = self.http = None
        else:
            self.http = kwargs.pop("http")
            self.library = Library(client, self)

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

        # AsyncIterable attrs
        self.__aiter_klass__ = Playlist
        self.__aiter_fetch__ = partial(
            self.__client.http.get_playlists, self.id, limit=50
        )

    def __repr__(self):
        return f"<spotify.User: {(self.display_name or self.id)!r}>"

    def __getattr__(self, attr):
        value = object.__getattribute__(self, attr)

        if (
            hasattr(value, "__ensure_http__")
            and getattr(self, "http", None) is not None
        ):

            @functools.wraps(value)
            def _raise(*args, **kwargs):
                raise AttributeError(
                    "User has not HTTP presence to perform API requests."
                )

            return _raise
        return value

    # Internals

    async def _get_top(self, klass: Type[T], kwargs: dict) -> List[T]:
        target = {Artist: "artists", Track: "tracks"}[klass]
        data = {
            key: value
            for key, value in kwargs.items()
            if key in ("limit", "offset", "time_range")
        }

        resp = await self.http.top_artists_or_tracks(target, **data)  # type: ignore

        return [klass(self.__client, item) for item in resp["items"]]

    ### Alternate constructors

    @classmethod
    async def from_code(
        cls, client: "spotify.Client", code: str, *, redirect_uri: str,
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

        raw = await client.http.request(route, headers=headers, params=payload)

        token = raw["access_token"]
        refresh_token = raw["refresh_token"]

        return await cls.from_token(client, token, refresh_token)

    @classmethod
    async def from_token(
        cls,
        client: "spotify.Client",
        token: Optional[str],
        refresh_token: Optional[str] = None,
    ):
        """Create a :class:`User` object from an access token.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        token : :class:`str`
            The access token to use for http requests.
        refresh_token : :class:`str`
            Used to acquire new token when it expires.
        """
        client_id = client.http.client_id
        client_secret = client.http.client_secret
        http = HTTPUserClient(client_id, client_secret, token, refresh_token)
        data = await http.current_user()
        return cls(client, data=data, http=http)

    @classmethod
    async def from_refresh_token(cls, client: "spotify.Client", refresh_token: str):
        """Create a :class:`User` object from a refresh token.
        It will poll the spotify API for a new access token and
        use that to initialize the spotify user.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        refresh_token: str
            Used to acquire token.
        """
        return await cls.from_token(client, None, refresh_token)

    ### Contextual methods

    @ensure_http
    async def currently_playing(self) -> Dict[str, Union[Track, Context, str]]:
        """Get the users currently playing track.

        Returns
        -------
        context, track : Dict[str, Union[Track, Context, str]]
            A tuple of the context and track.
        """
        data = await self.http.currently_playing()  # type: ignore

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
        player = Player(self.__client, self, await self.http.current_player())  # type: ignore
        return player

    @ensure_http
    async def get_devices(self) -> List[Device]:
        """Get information about the users avaliable devices.

        Returns
        -------
        devices : List[:class:`Device`]
            The devices the user has available.
        """
        data = await self.http.available_devices()  # type: ignore
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
        data = await self.http.recently_played()  # type: ignore
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
        data = await self.http.add_playlist_tracks(  # type: ignore
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
        await self.http.replace_playlist_tracks(  # type: ignore
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
        data = await self.http.remove_playlist_tracks(  # type: ignore
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
        data = await self.http.reorder_playlists_tracks(  # type: ignore
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

        await self.http.change_playlist_details(self.id, to_id(str(playlist)), **data)  # type: ignore

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

        playlist_data = await self.http.create_playlist(self.id, **data)  # type: ignore
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
        await self.http.follow_playlist(to_id(str(playlist)), public=public)  # type: ignore

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
        data = await self.http.get_playlists(self.id, limit=limit, offset=offset)  # type: ignore

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
            data = await self.http.get_playlists(self.id, limit=50, offset=offset)  # type: ignore

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
