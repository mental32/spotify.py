from .. import _clean_namespace
from .base import SpotifyBase, URIBase
from . import typing

# To avoid circular/impossible imports.
# We have to place "dead" refrences to
# other models, such as Album, Track and User e.g
# "Track: Optional[SpotifyBase] = None"
# so that the modules can resolve the 
# names correctly at compiletime then
# by runtime the dead refrences will have 
# been replaced with a refrence to the intended object.

from .common import Device, Context, Image
from .artist import Artist  # DEAD: Album Track
from .track import Track, PlaylistTrack  # DEAD: Album
from .player import Player
from .album import Album
from .library import Library
from .playlist import Playlist, PartialTracks  # DEAD: User
from .user import User

# swap the "dead" refrences
from . import artist, playlist, track
with _clean_namespace(locals(), 'track', 'artist', 'playlist'):
    setattr(artist, 'Album', Album)
    setattr(artist, 'Track', Track)
    setattr(playlist, 'User', User)
    setattr(track, 'Album', Album)

__all__ = ('User', 'Track', 'PlaylistTrack', 'Artist', 'Album', 'Playlist', 'PartialTracks', 'Library', 'Player', 'Device', 'Context', 'Image')
