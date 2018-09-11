__all__ = ('User', 'Track', 'PlaylistTrack', 'Artist', 'Album', 'Playlist', 'Library', 'Player', 'Device', 'Context', 'Image')

from spotify import _types

from .user import User
from .track import Track, PlaylistTrack
from .artist import Artist
from .album import Album
from .playlist import Playlist
from .library import Library
from .player import Player
from .common import Device, Context, Image

_types.update({
    'artist': Artist,
    'track': Track,
    'user': User,
    'playlist': Playlist,
    'album': Album,
    'library': Library,
    'playlist_track': PlaylistTrack
})
