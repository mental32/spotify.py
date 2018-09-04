from . import utils
from .utils import OAuth2

_types = utils._spotify__lookup()

from .errors import *
from .models import *

_types.update({
    'artist': Artist,
    'track': Track,
    'user': User,
    'playlist': Playlist,
    'album': Album,
    'library': Library,
    'playlist_track': PlaylistTrack
})

from .client import Client
from .http import HTTPClient, HTTPUserClient
from .local import LocalClient

__title__ = 'spotify'
__author__ = 'mental'
__license__ = 'MIT'
__version__ = '0.1.9'
