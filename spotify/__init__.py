from .utils import OAuth2, clean as _clean_namespace

from .errors import *
from .models import *
from .client import Client
from .models import SpotifyBase
from .http import HTTPClient, HTTPUserClient

__all__ = tuple(name for name in locals() if name[0] != '_')

__title__ = 'spotify'
__author__ = 'mental'
__license__ = 'MIT'
__version__ = '0.4.0'

_locals = locals()

with _clean_namespace(locals(), '_locals', '_clean_namespace'):
    _types = dict((name, _locals[name]) for name, obj in _locals.items() if isinstance(obj, type) and issubclass(obj, SpotifyBase))
    _types['HTTPClient'] = HTTPClient
    _types['HTTPUserClient'] = HTTPUserClient
