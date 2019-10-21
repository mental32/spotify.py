from typing import Union, Optional, List

from . import SpotifyBase, Context, Device, Track
from .typing import SomeURIs

Offset = Union[int, str, Track]
SomeDevice = Union[Device, str]


class Player(SpotifyBase):  # pylint: disable=too-many-instance-attributes
    """A Spotify Users current playback.

    Attributes
    ----------
    device : :class:`spotify.Device`
        The device that is currently active.
    repeat_state : :class:`str`
        "off", "track", "context"
    shuffle_state : :class:`bool`
        If shuffle is on or off.
    context : :class:`spotify.Context`
        The context of the current player.
    timestamp : :class:`int`
        Unix Millisecond Timestamp when data was fetched.
    progress_ms : :class:`int`
        Progress into the currently playing track.
        Can be None (e.g. If private session is enabled this will be None).
    is_playing : :class:`bool`
        If something is currently playing.
    item : :class:`spotify.Track`
        The currently playing track.
        Can be None (e.g. If private session is enabled this will be None).
    currently_playing_type : :class:`str`
        The object type of the currently playing item. #
        Can be one of "track", "episode", "ad" or "unknown".
    actions : List[:class:`str`]
        A list of disallowed actions.
    """

    def __init__(self, client, user, data):
        self.__client = client
        self.__user = user

        self.repeat_state = data.get("repeat_state", None)
        self.timestamp = data.pop("timestamp", None)
        self.progress_ms = data.pop("progress_ms", None)
        self.shuffle_state = data.pop("shuffle_state", None)
        self.is_playing = data.pop("is_playing", None)

        context = data.pop("context", None)
        if context:
            self.context = Context(context)

        device = data.pop("device", None)
        if device:
            self.device = Device(device)

        item = data.pop("item", None)
        if item:
            self.item = Track(client, item)

    def __repr__(self):
        return f"<spotify.Player: {self.user!r}>"

    # Properties

    @property
    def user(self):
        return self.__user

    # Public methods

    async def pause(self, *, device: Optional[SomeDevice] = None):
        """Pause playback on the user’s account.

        Parameters
        ----------
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.pause_playback(device_id=str(device))

    async def resume(self, *, device: Optional[SomeDevice] = None):
        """Resume playback on the user's account.

        Parameters
        ----------
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.play_playback(None, device_id=str(device))

    async def seek(self, pos, *, device: Optional[SomeDevice] = None):
        """Seeks to the given position in the user’s currently playing track.

        Parameters
        ----------
        pos : int
            The position in milliseconds to seek to.
            Must be a positive number.
            Passing in a position that is greater than the length of the track will cause the player to start playing the next song.
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.seek_playback(pos, device_id=str(device))

    async def set_repeat(self, state, *, device: Optional[SomeDevice] = None):
        """Set the repeat mode for the user’s playback.

        Parameters
        ----------
        state : str
            Options are repeat-track, repeat-context, and off
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.repeat_playback(state, device_id=str(device))

    async def set_volume(self, volume: int, *, device: Optional[SomeDevice] = None):
        """Set the volume for the user’s current playback device.

        Parameters
        ----------
        volume : int
            The volume to set. Must be a value from 0 to 100 inclusive.
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.set_playback_volume(volume, device_id=str(device))

    async def next(self, *, device: Optional[SomeDevice] = None):
        """Skips to next track in the user’s queue.

        Parameters
        ----------
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.skip_next(device_id=str(device))

    async def previous(self, *, device: Optional[SomeDevice] = None):
        """Skips to previous track in the user’s queue.

        Note that this will ALWAYS skip to the previous track, regardless of the current track’s progress.
        Returning to the start of the current track should be performed using :meth:`seek`

        Parameters
        ----------
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        return await self.user.http.skip_previous(device_id=str(device))

    async def play(
        self,
        *uris: SomeURIs,
        offset: Optional[Offset] = 0,
        device: Optional[SomeDevice] = None,
    ):
        """Start a new context or resume current playback on the user’s active device.

        The method treats a single argument as a Spotify context, such as a Artist, Album and playlist objects/URI.
        When called with multiple positional arguments they are interpreted as a array of Spotify Track objects/URIs.

        Parameters
        ----------
        *uris : SomeURI
            When a single argument is passed in that argument is treated as a context.
            Valid contexts are: albums, artists, playlists.
            Album, Artist and Playlist objects are accepted too.
            Otherwise when multiple arguments are passed in they,
            A sequence of Spotify Tracks or Track URIs to play.
        offset : Optional[:obj:`Offset`]
            Indicates from where in the context playback should start.
            Only available when `context` corresponds to an album or playlist object,
            or when the `uris` parameter is used. when an integer offset is zero based and can’t be negative.
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        context_uri: Union[List[str], str]

        if len(uris) > 1:
            # Regular uris paramter
            context_uri = [str(uri) for uri in uris]
        else:
            # Treat it as a context URI
            context_uri = str(uris[0])

        if device is not None:
            if not isinstance(device, (Device, str)):
                raise TypeError(
                    f"Expected `device` to either be a spotify.Device or a string. got {type(device)!r}"
                )

            device_id = str(device)

        await self.user.http.play_playback(
            context_uri, offset=offset, device_id=device_id
        )

    async def shuffle(
        self, state: Optional[bool] = None, *, device: Optional[SomeDevice] = None
    ):
        """shuffle on or off for user’s playback.

        Parameters
        ----------
        state : Optional[bool]
            if `True` then Shuffle user’s playback.
            else if `False` do not shuffle user’s playback.
        device : Optional[:obj:`SomeDevice`]
            The Device object or id of the device this command is targeting.
            If not supplied, the user’s currently active device is the target.
        """
        await self.user.http.shuffle_playback(state, device_id=str(device))

    async def transfer(self, device: SomeDevice, ensure_playback: bool = False):
        """Transfer playback to a new device and determine if it should start playing.

        Parameters
        ----------
        device : :obj:`SomeDevice`
            The device on which playback should be started/transferred.
        ensure_playback : bool
            if `True` ensure playback happens on new device.
            else keep the current playback state.
        """
        await self.user.http.transfer_player(str(device), play=ensure_playback)
