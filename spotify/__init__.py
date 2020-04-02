__version__ = "0.10.2"
__title__ = "spotify"
__author__ = "mental"
__license__ = "MIT"

from typing import Dict, Type

from .oauth import *
from .utils import clean as _clean_namespace
from .errors import *
from .models import *
from .client import *
from .models import SpotifyBase
from .http import HTTPClient, HTTPUserClient

__all__ = tuple(name for name in locals() if name[0] != "_")

_locals = locals()  # pylint: disable=invalid-name

_types: Dict[str, Type[Union[SpotifyBase, HTTPClient]]]
with _clean_namespace(locals(), "_locals", "_clean_namespace"):
    _types = dict(  # pylint: disable=invalid-name
        (name, _locals[name])
        for name, obj in _locals.items()
        if isinstance(obj, type) and issubclass(obj, SpotifyBase)
    )
    _types["HTTPClient"] = HTTPClient
    _types["HTTPUserClient"] = HTTPUserClient
