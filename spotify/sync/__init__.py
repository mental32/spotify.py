from spotify import *
from spotify import __all__, _types
from spotify.utils import clean as _clean_namespace

from . import models
from .models import Client, _install

with _clean_namespace(locals(), 'name', 'klass'):
    for name, klass in _install(_types):
        klass.__name__ = name
        locals()[name] = klass
        setattr(models, name, klass)
    else:
        Client._default_http_client = locals()['HTTPClient']
