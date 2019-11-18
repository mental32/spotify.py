from .oauth import *
from .utils import clean as _clean_namespace

__version__ = "0.8.2"  # noqa

from .errors import *
from .models import *
from .client import *
from .models import SpotifyBase
from .http import HTTPClient, HTTPUserClient

__all__ = tuple(name for name in locals() if name[0] != "_")

__title__ = "spotify"
__author__ = "mental"
__license__ = "MIT"

_locals = locals()  # pylint: disable=invalid-name

with _clean_namespace(locals(), "_locals", "_clean_namespace"):
    _types = dict(  # pylint: disable=invalid-name
        (name, _locals[name])
        for name, obj in _locals.items()
        if isinstance(obj, type) and issubclass(obj, SpotifyBase)
    )
    _types["HTTPClient"] = HTTPClient
    _types["HTTPUserClient"] = HTTPUserClient
