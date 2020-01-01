# pylint: skip-file

from spotify import *
from spotify import __all__, _types, Client
from spotify.utils import clean as _clean_namespace

from . import models
from .models import Client, Synchronous as _Sync


with _clean_namespace(locals(), "name", "base", "Mock"):
    for name, base in _types.items():

        class Mock(base, metaclass=_Sync):  # type: ignore
            __slots__ = {"__client_thread__"}

        Mock.__name__ = base.__name__
        Mock.__qualname__ = base.__qualname__
        Mock.__doc__ = base.__doc__

        locals()[name] = Mock
        setattr(models, name, Mock)

    Client._default_http_client = locals()[
        "HTTPClient"
    ]  # pylint: disable=protected-access
